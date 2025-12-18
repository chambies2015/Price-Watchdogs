from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging
import asyncio
from app.database import AsyncSessionLocal
from app.models.service import Service, CheckFrequency
from app.models.alert import Alert
from app.models.change_event import ChangeEvent
from app.services.snapshot_service import create_snapshot
from app.services.diff_service import process_new_snapshot
from app.services.email_service import send_alert_email

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def fetch_service_pages():
    logger.info("Starting page fetch job")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Service).where(Service.is_active == True)
            )
            services = result.scalars().all()
            
            for service in services:
                try:
                    if should_check_service(service):
                        logger.info(f"Checking service {service.id}: {service.name}")
                        snapshot = await create_snapshot(db, service)
                        
                        try:
                            change_event = await process_new_snapshot(db, snapshot)
                            if change_event:
                                logger.info(f"Detected change for service {service.id}: {change_event.change_type.value}")
                        except Exception as e:
                            logger.error(f"Error processing diff for service {service.id}: {e}")
                    else:
                        logger.debug(f"Skipping service {service.id}: not due for check")
                        
                except Exception as e:
                    logger.error(f"Error processing service {service.id}: {e}")
                    continue
                    
            logger.info(f"Completed page fetch job. Checked {len([s for s in services if should_check_service(s)])} services")
            
        except Exception as e:
            logger.error(f"Error in page fetch job: {e}")


def should_check_service(service: Service) -> bool:
    if not service.last_checked_at:
        return True
    
    now = datetime.utcnow()
    time_since_check = now - service.last_checked_at
    
    if service.check_frequency == CheckFrequency.daily:
        return time_since_check >= timedelta(hours=24)
    elif service.check_frequency == CheckFrequency.weekly:
        return time_since_check >= timedelta(days=7)
    
    return False


async def dispatch_pending_alerts():
    logger.info("Starting alert dispatch job")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Alert)
                .where(Alert.sent_at.is_(None))
                .options(
                    selectinload(Alert.change_event).selectinload(ChangeEvent.service),
                    selectinload(Alert.change_event).selectinload(ChangeEvent.old_snapshot),
                    selectinload(Alert.change_event).selectinload(ChangeEvent.new_snapshot),
                    selectinload(Alert.user)
                )
                .limit(10)
            )
            pending_alerts = result.scalars().all()
            
            if not pending_alerts:
                logger.debug("No pending alerts to dispatch")
                return
            
            logger.info(f"Processing {len(pending_alerts)} pending alerts")
            
            sent_count = 0
            error_count = 0
            
            for alert in pending_alerts:
                try:
                    await db.refresh(alert)
                    change_event = alert.change_event
                    service = change_event.service
                    user = alert.user
                    old_snapshot = change_event.old_snapshot
                    new_snapshot = change_event.new_snapshot
                    
                    if not new_snapshot:
                        logger.warning(f"New snapshot not found for alert {alert.id}")
                        error_count += 1
                        continue
                    
                    success = await send_alert_email(
                        change_event,
                        service,
                        user,
                        old_snapshot,
                        new_snapshot
                    )
                    
                    if success:
                        alert.sent_at = datetime.utcnow()
                        await db.commit()
                        sent_count += 1
                        logger.info(f"Successfully dispatched alert {alert.id}")
                    else:
                        error_count += 1
                        logger.warning(f"Failed to send email for alert {alert.id}")
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing alert {alert.id}: {e}")
                    error_count += 1
                    continue
            
            logger.info(f"Alert dispatch job completed: {sent_count} sent, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Error in alert dispatch job: {e}")


def start_scheduler():
    scheduler.add_job(
        fetch_service_pages,
        trigger=IntervalTrigger(hours=1),
        id='fetch_service_pages',
        name='Fetch service pages and create snapshots',
        replace_existing=True
    )
    
    scheduler.add_job(
        dispatch_pending_alerts,
        trigger=IntervalTrigger(minutes=5),
        id='dispatch_pending_alerts',
        name='Dispatch pending email alerts',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

