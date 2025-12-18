from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.database import AsyncSessionLocal
from app.models.service import Service, CheckFrequency
from app.services.snapshot_service import create_snapshot
from app.services.diff_service import process_new_snapshot

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


def start_scheduler():
    scheduler.add_job(
        fetch_service_pages,
        trigger=IntervalTrigger(hours=1),
        id='fetch_service_pages',
        name='Fetch service pages and create snapshots',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

