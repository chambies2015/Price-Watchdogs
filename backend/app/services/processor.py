import hashlib
import re
from typing import Tuple
from bs4 import BeautifulSoup
import bleach
import logging

logger = logging.getLogger(__name__)

ALLOWED_TAGS = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'tbody', 'thead']
ALLOWED_ATTRIBUTES = {'*': ['class', 'id']}

PRICING_SELECTORS = [
    '[class*="pric"]',
    '[class*="plan"]',
    '[class*="tier"]',
    '[class*="package"]',
    '[class*="subscription"]',
    '[class*="cost"]',
    '[class*="amount"]',
    '[id*="pric"]',
    '[id*="plan"]',
    '[id*="tier"]',
    '[id*="package"]',
    '[data-testid*="pric"]',
    '[data-testid*="plan"]',
    '[data-testid*="tier"]',
    'table',
]

NOISE_PATTERNS = [
    r'\d{1,2}:\d{2}:\d{2}',
    r'\d{1,2}/\d{1,2}/\d{2,4}',
    r'\d{4}-\d{2}-\d{2}',
    r'Updated:\s*\w+\s*\d{1,2},?\s*\d{4}',
    r'Last updated:.*',
    r'Cookie',
    r'Accept all cookies',
    r'We use cookies',
    r'Terms apply',
    r'Plans available with or without ads\*+',
]


def sanitize_html(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    
    for tag in soup(['script', 'style', 'iframe', 'noscript', 'meta', 'link']):
        tag.decompose()
    
    for tag in soup.find_all(class_=re.compile(r'(ad|banner|cookie|tracking|analytics)', re.I)):
        tag.decompose()
    
    for tag in soup.find_all(id=re.compile(r'(ad|banner|cookie|tracking|analytics)', re.I)):
        tag.decompose()
    
    clean_html = bleach.clean(
        str(soup),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return clean_html


def extract_pricing_content(html: str, custom_selector: str = None) -> str:
    soup = BeautifulSoup(html, 'lxml')
    
    if custom_selector:
        selectors = [custom_selector]
    else:
        selectors = PRICING_SELECTORS
    
    extracted_elements = []
    
    for selector in selectors:
        try:
            elements = soup.select(selector)
            extracted_elements.extend(elements)
        except Exception as e:
            logger.warning(f"Error with selector {selector}: {e}")
            continue
    
    if extracted_elements:
        pricing_html = ' '.join(str(elem) for elem in extracted_elements)
        if pricing_html:
            return pricing_html
    
    price_pattern = re.compile(r'\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+', re.IGNORECASE)
    
    all_elements = soup.find_all(['div', 'section', 'article', 'table', 'tr', 'td', 'p', 'span', 'li'])
    pricing_elements = []
    
    for elem in all_elements:
        text = elem.get_text()
        if text and price_pattern.search(text):
            pricing_elements.append(elem)
    
    if pricing_elements:
        logger.info(f"Found {len(pricing_elements)} elements containing prices via pattern matching")
        pricing_html = ' '.join(str(elem) for elem in pricing_elements)
        return pricing_html
    
    return soup.get_text()


def extract_structured_pricing(text: str) -> str:
    price_pattern = re.compile(r'\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+')

    text = re.sub(r'\s+', ' ', text).strip()
    price_matches = list(price_pattern.finditer(text))
    if not price_matches:
        return text[:500] if len(text) > 500 else text

    def unit_for(after: str) -> str:
        m = re.search(r'(?:/|per)\s*(month|mo|year|yr)\b', after, re.IGNORECASE)
        if m:
            u = m.group(1).lower()
            return ' / month' if u in ('month', 'mo') else ' / year'
        if re.search(r'\bmonthly\b', after, re.IGNORECASE):
            return ' / month'
        if re.search(r'\b(annual|yearly)\b', after, re.IGNORECASE):
            return ' / year'
        return ''

    def pick_plan(window: str, price_rel: int) -> str:
        candidates = []
        for m in re.finditer(r'([A-Za-z0-9][A-Za-z0-9+,&/\-\s]{2,90}?\b(?:Bundle|Plan|Tier)\b)', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return ''

    def clean_plan(plan: str) -> str:
        plan = re.sub(r'\s+', ' ', plan).strip(' -—|')
        plan = re.sub(r'^(Starting at|From)\s+', '', plan, flags=re.IGNORECASE)
        plan = re.sub(r'\b(Terms apply|Plans available with or without ads)\b.*$', '', plan, flags=re.IGNORECASE).strip()
        return plan

    lines = []
    seen = set()
    for match in price_matches:
        price = match.group(0)
        after = text[match.end():match.end() + 80]
        unit = unit_for(after)

        w_start = max(0, match.start() - 450)
        w_end = min(len(text), match.end() + 250)
        window = text[w_start:w_end]
        price_rel = match.start() - w_start

        plan = clean_plan(pick_plan(window, price_rel))
        key = (plan.lower(), price, unit)
        if key in seen:
            continue
        seen.add(key)

        if plan:
            lines.append(f"{plan} — {price}{unit}")

    if lines:
        return '\n\n'.join(f"• {line}" for line in lines)

    unique_prices = []
    seen_prices = set()
    for match in price_matches:
        p = match.group(0)
        if p not in seen_prices:
            unique_prices.append(p)
            seen_prices.add(p)
    return "Prices found: " + ", ".join(unique_prices)


def normalize_text(text: str, preserve_newlines: bool = False) -> str:
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    if preserve_newlines:
        lines = text.split('\n')
        lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in lines]
        text = '\n'.join([line for line in lines if line])
    else:
        text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    
    return text


def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def process_html(html: str, custom_selector: str = None) -> Tuple[str, str, str]:
    raw_hash = generate_hash(html)
    
    logger.info(f"Processing HTML: {len(html)} bytes")
    
    pricing_content = extract_pricing_content(html, custom_selector)
    logger.info(f"Extracted pricing content: {len(pricing_content)} bytes")
    
    soup = BeautifulSoup(pricing_content, 'lxml')
    text_content = soup.get_text(separator=' ', strip=True)
    logger.info(f"Text content extracted: {len(text_content)} chars")
    
    structured_content = extract_structured_pricing(text_content)
    logger.info(f"Structured pricing: {len(structured_content)} chars")
    
    normalized = normalize_text(structured_content, preserve_newlines=True)
    logger.info(f"Normalized content: {len(normalized)} chars")
    
    normalized_hash = generate_hash(normalized)
    
    return raw_hash, normalized_hash, normalized

