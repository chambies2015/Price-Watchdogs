import httpx
import logging
import json
from typing import Optional
from app.models.change_event import ChangeEvent
from app.models.service import Service
from app.models.user import User
from app.models.snapshot import Snapshot

logger = logging.getLogger(__name__)


def format_slack_message(
    change_event: ChangeEvent,
    service: Service,
    user: User,
    old_snapshot: Optional[Snapshot],
    new_snapshot: Snapshot
) -> dict:
    change_type_labels = {
        "price_increase": "Price Increase",
        "price_decrease": "Price Decrease",
        "new_plan_added": "New Plan Added",
        "plan_removed": "Plan Removed",
        "free_tier_removed": "Free Tier Removed",
        "unknown": "Change Detected"
    }
    
    change_label = change_type_labels.get(change_event.change_type.value, "Change Detected")
    color = "danger" if change_event.change_type.value == "price_increase" else "good"
    
    fields = [
        {
            "title": "Service",
            "value": service.name,
            "short": True
        },
        {
            "title": "URL",
            "value": service.url,
            "short": True
        },
        {
            "title": "Change Type",
            "value": change_label,
            "short": True
        },
        {
            "title": "Confidence",
            "value": f"{change_event.confidence_score:.0%}",
            "short": True
        },
        {
            "title": "Summary",
            "value": change_event.summary,
            "short": False
        }
    ]
    
    return {
        "attachments": [
            {
                "color": color,
                "title": f"Price Change Detected: {service.name}",
                "fields": fields,
                "footer": "Price Watchdogs",
                "ts": int(change_event.created_at.timestamp())
            }
        ]
    }


async def send_slack_webhook(webhook_url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            if response.status_code == 200:
                logger.info("Successfully sent Slack webhook")
                return True
            logger.error(f"Failed to send Slack webhook: {response.status_code} - {response.text}")
            return False
    except httpx.TimeoutException:
        logger.error("Timeout sending Slack webhook")
        return False
    except Exception as e:
        logger.error(f"Error sending Slack webhook: {e}")
        return False


async def send_alert_to_slack(
    change_event: ChangeEvent,
    service: Service,
    user: User,
    old_snapshot: Optional[Snapshot],
    new_snapshot: Snapshot
) -> bool:
    if not service.slack_webhook_url:
        return False
    
    payload = format_slack_message(change_event, service, user, old_snapshot, new_snapshot)
    return await send_slack_webhook(service.slack_webhook_url, payload)
