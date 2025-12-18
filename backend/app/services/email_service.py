import httpx
import logging
import html
from typing import Optional
from datetime import datetime
from app.config import settings
from app.models.change_event import ChangeEvent
from app.models.service import Service
from app.models.user import User
from app.models.snapshot import Snapshot

logger = logging.getLogger(__name__)


def render_alert_email(
    change_event: ChangeEvent,
    service: Service,
    user: User,
    old_snapshot: Optional[Snapshot],
    new_snapshot: Snapshot
) -> tuple[str, str]:
    change_type_labels = {
        "price_increase": "Price Increase",
        "price_decrease": "Price Decrease",
        "new_plan_added": "New Plan Added",
        "plan_removed": "Plan Removed",
        "free_tier_removed": "Free Tier Removed",
        "unknown": "Change Detected"
    }
    
    change_label = change_type_labels.get(change_event.change_type.value, "Change Detected")
    diff_url = f"{settings.frontend_base_url}/services/{service.id}/changes/{change_event.id}"
    
    old_content_preview = ""
    new_content_preview = ""
    
    if old_snapshot:
        old_lines = old_snapshot.normalized_content.splitlines()[:10]
        old_content_preview = "\n".join(old_lines)
        if len(old_snapshot.normalized_content.splitlines()) > 10:
            old_content_preview += "\n..."
        old_content_preview = html.escape(old_content_preview)
    
    new_lines = new_snapshot.normalized_content.splitlines()[:10]
    new_content_preview = "\n".join(new_lines)
    if len(new_snapshot.normalized_content.splitlines()) > 10:
        new_content_preview += "\n..."
    new_content_preview = html.escape(new_content_preview)
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .content {{ background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .change-type {{ display: inline-block; padding: 5px 10px; background-color: #007bff; color: white; border-radius: 3px; font-weight: bold; }}
        .confidence {{ color: #666; font-size: 0.9em; }}
        .comparison {{ margin-top: 20px; }}
        .old-content, .new-content {{ padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .old-content {{ background-color: #fff3cd; border-left: 3px solid #ffc107; }}
        .new-content {{ background-color: #d1ecf1; border-left: 3px solid #0c5460; }}
        .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Price Change Detected</h1>
        </div>
        <div class="content">
            <h2>{html.escape(service.name)}</h2>
            <p><a href="{html.escape(service.url)}">{html.escape(service.url)}</a></p>
            
            <div style="margin: 20px 0;">
                <span class="change-type">{change_label}</span>
                <span class="confidence"> (Confidence: {change_event.confidence_score:.0%})</span>
            </div>
            
            <p><strong>Summary:</strong> {html.escape(change_event.summary)}</p>
            <p><strong>Detected:</strong> {change_event.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <div class="comparison">
                <h3>Content Comparison</h3>
                {f'<div class="old-content"><strong>Before:</strong><pre style="white-space: pre-wrap;">{old_content_preview}</pre></div>' if old_content_preview else ''}
                <div class="new-content"><strong>After:</strong><pre style="white-space: pre-wrap;">{new_content_preview}</pre></div>
            </div>
            
            <a href="{diff_url}" class="button">View Full Details</a>
        </div>
        
        <div class="footer">
            <p>This is an automated alert from Price Watchdogs.</p>
            <p>You can manage your alert settings in your dashboard.</p>
        </div>
    </div>
</body>
</html>
"""
    
    text_content = f"""
Price Change Detected: {service.name}

Service URL: {service.url}

Change Type: {change_label}
Confidence: {change_event.confidence_score:.0%}
Summary: {change_event.summary}
Detected: {change_event.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

{f'Before:\n{old_content_preview}\n' if old_content_preview else ''}After:
{new_content_preview}

View full details: {diff_url}

---
This is an automated alert from Price Watchdogs.
You can manage your alert settings in your dashboard.
"""
    
    return html_content, text_content


async def send_alert_email(
    change_event: ChangeEvent,
    service: Service,
    user: User,
    old_snapshot: Optional[Snapshot],
    new_snapshot: Snapshot
) -> bool:
    if not settings.mailgun_api_key or not settings.mailgun_domain or not settings.mailgun_from_email:
        logger.warning("Mailgun configuration missing, skipping email send")
        return False
    
    try:
        html_content, text_content = render_alert_email(
            change_event, service, user, old_snapshot, new_snapshot
        )
        
        subject = f"Price Change Detected: {service.name}"
        
        mailgun_url = f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                mailgun_url,
                auth=("api", settings.mailgun_api_key),
                data={
                    "from": settings.mailgun_from_email,
                    "to": user.email,
                    "subject": subject,
                    "text": text_content,
                    "html": html_content
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent alert email to {user.email} for change event {change_event.id}")
                return True
            else:
                logger.error(f"Failed to send email via Mailgun: {response.status_code} - {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error(f"Timeout sending email to {user.email} for change event {change_event.id}")
        return False
    except Exception as e:
        logger.error(f"Error sending email to {user.email} for change event {change_event.id}: {e}")
        return False

