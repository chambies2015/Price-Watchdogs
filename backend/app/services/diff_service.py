import difflib
import re
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent, ChangeType
from app.models.service import Service
import uuid

logger = logging.getLogger(__name__)

PRICE_PATTERNS = [
    r'\$\s*\d+(?:\.\d{2})?',
    r'€\s*\d+(?:\.\d{2})?',
    r'£\s*\d+(?:\.\d{2})?',
    r'¥\s*\d+(?:\.\d{2})?',
    r'\d+(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY)',
]

PLAN_KEYWORDS = ['plan', 'tier', 'package', 'subscription', 'pricing']
FREE_TIER_KEYWORDS = ['free', '$0', '€0', '£0', '¥0', 'trial', 'no cost', 'zero cost']

CONFIDENCE_THRESHOLD = 0.6


def extract_prices(text: str) -> List[str]:
    prices = []
    for pattern in PRICE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        prices.extend(matches)
    return prices


def extract_plan_names(text: str) -> List[str]:
    plan_names = []
    lines = text.lower().split('\n')
    
    exclude_phrases = ['pricing information', 'pricing page', 'pricing details']
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        if any(phrase in line_stripped for phrase in exclude_phrases):
            continue
        
        for keyword in PLAN_KEYWORDS:
            if keyword == 'pricing':
                if 'pricing:' in line_stripped or 'pricing -' in line_stripped or extract_prices(line_stripped):
                    plan_names.append(line_stripped)
                    break
            else:
                if keyword in line_stripped:
                    plan_names.append(line_stripped)
                    break
    
    return plan_names


def has_free_tier(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FREE_TIER_KEYWORDS)


def generate_diff(old_content: str, new_content: str) -> Tuple[List[str], List[str], List[str]]:
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    
    added = []
    removed = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            removed.extend(old_lines[i1:i2])
        elif tag == 'insert':
            added.extend(new_lines[j1:j2])
        elif tag == 'replace':
            removed.extend(old_lines[i1:i2])
            added.extend(new_lines[j1:j2])
    
    changed = list(set(added + removed))
    
    return added, removed, changed


def classify_change(old_content: str, new_content: str, added: List[str], removed: List[str]) -> Tuple[ChangeType, str, float]:
    old_prices = extract_prices(old_content)
    new_prices = extract_prices(new_content)
    
    added_text = ' '.join(added)
    removed_text = ' '.join(removed)
    
    old_plans = extract_plan_names(old_content)
    new_plans = extract_plan_names(new_content)
    
    old_has_free = has_free_tier(old_content)
    new_has_free = has_free_tier(new_content)
    
    if old_has_free and not new_has_free:
        summary = "Free tier has been removed from the pricing page"
        return ChangeType.free_tier_removed, summary, 0.9
    
    if len(new_plans) > len(old_plans):
        new_plan_names = set(new_plans) - set(old_plans)
        if new_plan_names:
            summary = f"New plan added: {', '.join(list(new_plan_names)[:3])}"
            return ChangeType.new_plan_added, summary, 0.75
    
    if len(old_plans) > len(new_plans):
        removed_plan_names = set(old_plans) - set(new_plans)
        if removed_plan_names:
            summary = f"Plan removed: {', '.join(list(removed_plan_names)[:3])}"
            return ChangeType.plan_removed, summary, 0.75
    
    if old_prices and new_prices:
        old_price_nums = []
        new_price_nums = []
        
        for price in old_prices:
            num_match = re.search(r'\d+(?:\.\d{2})?', price)
            if num_match:
                old_price_nums.append(float(num_match.group()))
        
        for price in new_prices:
            num_match = re.search(r'\d+(?:\.\d{2})?', price)
            if num_match:
                new_price_nums.append(float(num_match.group()))
        
        if old_price_nums and new_price_nums:
            avg_old = sum(old_price_nums) / len(old_price_nums)
            avg_new = sum(new_price_nums) / len(new_price_nums)
            
            if avg_new > avg_old:
                price_diff = avg_new - avg_old
                summary = f"Price increase detected: average price increased by ${price_diff:.2f}"
                return ChangeType.price_increase, summary, 0.85
            elif avg_new < avg_old:
                price_diff = avg_old - avg_new
                summary = f"Price decrease detected: average price decreased by ${price_diff:.2f}"
                return ChangeType.price_decrease, summary, 0.85
    
    added_prices_in_diff = extract_prices(added_text)
    removed_prices_in_diff = extract_prices(removed_text)
    
    if added_prices_in_diff and removed_prices_in_diff:
        summary = f"Pricing changes detected: {len(removed_prices_in_diff)} prices removed, {len(added_prices_in_diff)} prices added"
        return ChangeType.price_increase, summary, 0.7
    
    if len(added) > 0 or len(removed) > 0:
        change_size = len(added) + len(removed)
        summary = f"Content change detected: {len(removed)} lines removed, {len(added)} lines added"
        
        confidence = min(0.5, 0.3 + (change_size * 0.01))
        
        return ChangeType.unknown, summary, confidence
    
    return ChangeType.unknown, "Unknown change detected", 0.3


async def compare_snapshots(
    db: AsyncSession,
    old_snapshot: Snapshot,
    new_snapshot: Snapshot
) -> Optional[ChangeEvent]:
    if old_snapshot.normalized_content_hash == new_snapshot.normalized_content_hash:
        logger.info(f"No content change detected between snapshots {old_snapshot.id} and {new_snapshot.id}")
        return None
    
    added, removed, changed = generate_diff(
        old_snapshot.normalized_content,
        new_snapshot.normalized_content
    )
    
    change_type, summary, confidence = classify_change(
        old_snapshot.normalized_content,
        new_snapshot.normalized_content,
        added,
        removed
    )
    
    if confidence < CONFIDENCE_THRESHOLD:
        logger.info(f"Change confidence {confidence} below threshold {CONFIDENCE_THRESHOLD}, skipping")
        return None
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=new_snapshot.service_id,
        old_snapshot_id=old_snapshot.id,
        new_snapshot_id=new_snapshot.id,
        change_type=change_type,
        summary=summary,
        confidence_score=confidence
    )
    
    db.add(change_event)
    await db.commit()
    await db.refresh(change_event)
    
    logger.info(f"Created ChangeEvent {change_event.id}: {change_type.value} with confidence {confidence}")
    
    try:
        from app.services.alert_service import create_alert_for_change_event
        await create_alert_for_change_event(db, change_event)
    except Exception as e:
        logger.error(f"Error creating alert for change event {change_event.id}: {e}")
    
    return change_event


async def process_new_snapshot(
    db: AsyncSession,
    new_snapshot: Snapshot
) -> Optional[ChangeEvent]:
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.service_id == new_snapshot.service_id)
        .where(Snapshot.id != new_snapshot.id)
        .order_by(Snapshot.created_at.desc())
        .limit(1)
    )
    old_snapshot = result.scalar_one_or_none()
    
    if not old_snapshot:
        logger.info(f"No previous snapshot found for service {new_snapshot.service_id}")
        return None
    
    return await compare_snapshots(db, old_snapshot, new_snapshot)

