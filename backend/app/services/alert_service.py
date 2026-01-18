from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid
from datetime import datetime, timedelta
from app.models.alert import Alert
from app.models.change_event import ChangeEvent
from app.models.service import Service
from app.models.user import User

logger = logging.getLogger(__name__)

DEFAULT_ALERT_CAP = 10
ALERT_WINDOW_HOURS = 24


async def reset_alert_count_if_needed(db: AsyncSession, service: Service) -> None:
    if service.last_alert_reset is None:
        service.last_alert_reset = datetime.utcnow()
        service.alert_count_24h = 0
        await db.commit()
        return
    
    hours_since_reset = (datetime.utcnow() - service.last_alert_reset).total_seconds() / 3600
    if hours_since_reset >= ALERT_WINDOW_HOURS:
        service.alert_count_24h = 0
        service.last_alert_reset = datetime.utcnow()
        await db.commit()


async def check_alert_cap(db: AsyncSession, service: Service) -> bool:
    await reset_alert_count_if_needed(db, service)
    return service.alert_count_24h < DEFAULT_ALERT_CAP


async def create_alert_for_change_event(
    db: AsyncSession,
    change_event: ChangeEvent
) -> Optional[Alert]:
    result = await db.execute(
        select(Service).where(Service.id == change_event.service_id)
    )
    service = result.scalar_one_or_none()
    
    if not service:
        logger.warning(f"Service {change_event.service_id} not found for change event {change_event.id}")
        return None
    
    if not service.alerts_enabled:
        logger.debug(f"Alerts disabled for service {service.id}, skipping alert creation")
        return None
    
    if change_event.confidence_score < service.alert_confidence_threshold:
        logger.debug(
            f"Confidence score {change_event.confidence_score} below threshold "
            f"{service.alert_confidence_threshold} for service {service.id}"
        )
        return None
    
    if not await check_alert_cap(db, service):
        logger.warning(
            f"Alert cap reached for service {service.id} ({service.alert_count_24h}/{DEFAULT_ALERT_CAP}), skipping alert"
        )
        return None
    
    result = await db.execute(
        select(Alert).where(
            Alert.change_event_id == change_event.id,
            Alert.user_id == service.user_id
        )
    )
    existing_alert = result.scalar_one_or_none()
    
    if existing_alert:
        logger.debug(f"Alert already exists for change event {change_event.id} and user {service.user_id}")
        return existing_alert
    
    service.alert_count_24h += 1
    if service.last_alert_reset is None:
        service.last_alert_reset = datetime.utcnow()
    
    alert = Alert(
        id=uuid.uuid4(),
        change_event_id=change_event.id,
        user_id=service.user_id,
        sent_at=None
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    logger.info(f"Created alert {alert.id} for change event {change_event.id} and user {service.user_id}")
    
    return alert

