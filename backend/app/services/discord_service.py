import httpx
import logging
from typing import Optional
from app.models.change_event import ChangeEvent
from app.models.service import Service
from app.models.user import User
from app.models.snapshot import Snapshot

logger = logging.getLogger(__name__)


def format_discord_embed(
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
    color = 15158332 if change_event.change_type.value == "price_increase" else 3066993
    
    return {
        "embeds": [
            {
                "title": f"Price Change Detected: {service.name}",
                "description": change_event.summary,
                "color": color,
                "fields": [
                    {
                        "name": "Service",
                        "value": service.name,
                        "inline": True
                    },
                    {
                        "name": "URL",
                        "value": service.url,
                        "inline": True
                    },
                    {
                        "name": "Change Type",
                        "value": change_label,
                        "inline": True
                    },
                    {
                        "name": "Confidence",
                        "value": f"{change_event.confidence_score:.0%}",
                        "inline": True
                    }
                ],
                "timestamp": change_event.created_at.isoformat(),
                "footer": {
                    "text": "Price Watchdogs"
                }
            }
        ]
    }


async def send_discord_webhook(webhook_url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            if response.status_code in (200, 204):
                logger.info("Successfully sent Discord webhook")
                return True
            logger.error(f"Failed to send Discord webhook: {response.status_code} - {response.text}")
            return False
    except httpx.TimeoutException:
        logger.error("Timeout sending Discord webhook")
        return False
    except Exception as e:
        logger.error(f"Error sending Discord webhook: {e}")
        return False


async def send_alert_to_discord(
    change_event: ChangeEvent,
    service: Service,
    user: User,
    old_snapshot: Optional[Snapshot],
    new_snapshot: Snapshot
) -> bool:
    if not service.discord_webhook_url:
        return False
    
    payload = format_discord_embed(change_event, service, user, old_snapshot, new_snapshot)
    return await send_discord_webhook(service.discord_webhook_url, payload)
