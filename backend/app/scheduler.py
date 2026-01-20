from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging
import asyncio
from typing import Dict, List, Any
from uuid import UUID
from app.database import AsyncSessionLocal
from app.models.service import Service, CheckFrequency
from app.models.alert import Alert
from app.models.change_event import ChangeEvent
from app.models.snapshot import Snapshot
from app.services.snapshot_service import create_snapshot
from app.services.diff_service import process_new_snapshot
from app.services.email_service import send_alert_email
from app.services.slack_service import send_alert_to_slack
from app.services.discord_service import send_alert_to_discord
from app.services.cleanup_service import cleanup_old_snapshots

logger = logging.getLogger(__name__)

incident_history: List[Dict[str, Any]] = []


def record_incident(incident_type: str, description: str) -> None:
    incident = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": incident_type,
        "description": description
    }
    incident_history.append(incident)
    if len(incident_history) > 100:
        incident_history.pop(0)

scheduler = AsyncIOScheduler()

job_metrics: Dict[str, List[Dict[str, Any]]] = {}

"""
Background Job Scheduler

This module manages all background jobs using APScheduler:
- fetch_service_pages: Runs hourly to fetch and snapshot service pages
- dispatch_pending_alerts: Runs every 5 minutes to send pending email alerts
- cleanup_snapshots: Runs weekly (Sunday 2 AM) to clean up old snapshots

All jobs are automatically started when the FastAPI application starts.
Job metrics are tracked in the job_metrics dictionary for monitoring.
"""


async def process_service_with_retry(
    db: AsyncSession,
    service: Service,
    max_retries: int = 3
) -> tuple[bool, str]:
    for attempt in range(max_retries):
        try:
            if not should_check_service(service):
                return True, "skipped_not_due"
            
            snapshot, created_new = await create_snapshot(db, service)
            
            try:
                if created_new:
                    change_event = await process_new_snapshot(db, snapshot)
                    if change_event:
                        logger.info(f"Detected change for service {service.id}: {change_event.change_type.value}")
            except Exception as e:
                logger.error(f"Error processing diff for service {service.id}: {e}")
            
            return True, "success"
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} for service {service.id} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to process service {service.id} after {max_retries} attempts: {e}")
                return False, str(e)
    
    return False, "max_retries_exceeded"


async def fetch_service_pages():
    job_id = f"fetch_pages_{datetime.utcnow().isoformat()}"
    start_time = datetime.utcnow()
    
    logger.info(f"Starting page fetch job {job_id}")
    
    metrics = {
        "job_id": job_id,
        "job_name": "fetch_service_pages",
        "started_at": start_time,
        "services_processed": 0,
        "success_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "errors": []
    }
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Service).where(Service.is_active == True)
            )
            all_services = result.scalars().all()
            
            services_to_check = [s for s in all_services if should_check_service(s)]
            metrics["services_processed"] = len(services_to_check)
            
            batch_size = 5
            delay_between_batches = 2
            
            for i in range(0, len(services_to_check), batch_size):
                batch = services_to_check[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} services)")
                
                tasks = [process_service_with_retry(db, service) for service in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for service, result in zip(batch, results):
                    if isinstance(result, Exception):
                        metrics["error_count"] += 1
                        error_msg = f"Service {service.id}: {str(result)}"
                        metrics["errors"].append(error_msg)
                        logger.error(error_msg)
                    else:
                        success, status = result
                        if success:
                            if status == "skipped_not_due":
                                metrics["skipped_count"] += 1
                            else:
                                metrics["success_count"] += 1
                        else:
                            metrics["error_count"] += 1
                            error_msg = f"Service {service.id}: {status}"
                            metrics["errors"].append(error_msg)
                
                if i + batch_size < len(services_to_check):
                    await asyncio.sleep(delay_between_batches)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            metrics["completed_at"] = end_time
            metrics["duration_seconds"] = duration
            metrics["status"] = "completed"
            
            logger.info(
                f"Page fetch job {job_id} completed in {duration:.2f}s: "
                f"{metrics['success_count']} succeeded, {metrics['error_count']} failed, "
                f"{metrics['skipped_count']} skipped"
            )
            
            if job_id not in job_metrics:
                job_metrics[job_id] = []
            job_metrics[job_id].append(metrics)
            
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        metrics["completed_at"] = end_time
        metrics["duration_seconds"] = duration
        metrics["status"] = "failed"
        metrics["errors"].append(f"Job failed: {str(e)}")
        
        logger.error(f"Error in page fetch job {job_id}: {e}")
        record_incident("service_fetch_failure", f"Page fetch job failed: {str(e)}")
        
        if job_id not in job_metrics:
            job_metrics[job_id] = []
        job_metrics[job_id].append(metrics)


def should_check_service(service: Service) -> bool:
    if not service.last_checked_at:
        return True
    
    now = datetime.utcnow()
    time_since_check = now - service.last_checked_at
    
    if service.check_frequency == CheckFrequency.daily:
        return time_since_check >= timedelta(hours=24)
    elif service.check_frequency == CheckFrequency.weekly:
        return time_since_check >= timedelta(days=7)
    elif service.check_frequency == CheckFrequency.twice_daily:
        return time_since_check >= timedelta(hours=12)
    
    return False


async def dispatch_pending_alerts():
    job_id = f"dispatch_alerts_{datetime.utcnow().isoformat()}"
    start_time = datetime.utcnow()
    
    logger.info(f"Starting alert dispatch job {job_id}")
    
    metrics = {
        "job_id": job_id,
        "job_name": "dispatch_pending_alerts",
        "started_at": start_time,
        "alerts_processed": 0,
        "success_count": 0,
        "error_count": 0,
        "errors": []
    }
    
    try:
        async with AsyncSessionLocal() as db:
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
                logger.debug(f"No pending alerts to dispatch for job {job_id}")
                metrics["status"] = "completed"
                metrics["completed_at"] = datetime.utcnow()
                metrics["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
                return
            
            metrics["alerts_processed"] = len(pending_alerts)
            logger.info(f"Processing {len(pending_alerts)} pending alerts for job {job_id}")
            
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
                        metrics["error_count"] += 1
                        metrics["errors"].append(f"Alert {alert.id}: New snapshot not found")
                        continue
                    
                    channels_sent = []
                    email_success = await send_alert_email(
                        change_event,
                        service,
                        user,
                        old_snapshot,
                        new_snapshot
                    )
                    if email_success:
                        channels_sent.append("email")
                    
                    if service.slack_webhook_url:
                        slack_success = await send_alert_to_slack(
                            change_event,
                            service,
                            user,
                            old_snapshot,
                            new_snapshot
                        )
                        if slack_success:
                            channels_sent.append("slack")
                    
                    if service.discord_webhook_url:
                        discord_success = await send_alert_to_discord(
                            change_event,
                            service,
                            user,
                            old_snapshot,
                            new_snapshot
                        )
                        if discord_success:
                            channels_sent.append("discord")
                    
                    if channels_sent:
                        alert.sent_at = datetime.utcnow()
                        await db.commit()
                        metrics["success_count"] += 1
                        logger.info(f"Successfully dispatched alert {alert.id} via {', '.join(channels_sent)}")
                    else:
                        metrics["error_count"] += 1
                        metrics["errors"].append(f"Alert {alert.id}: All channel sends failed")
                        logger.warning(f"Failed to send alert {alert.id} via any channel")
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing alert {alert.id}: {e}")
                    metrics["error_count"] += 1
                    metrics["errors"].append(f"Alert {alert.id}: {str(e)}")
                    continue
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            metrics["completed_at"] = end_time
            metrics["duration_seconds"] = duration
            metrics["status"] = "completed"
            
            logger.info(
                f"Alert dispatch job {job_id} completed in {duration:.2f}s: "
                f"{metrics['success_count']} sent, {metrics['error_count']} errors"
            )
            
            if job_id not in job_metrics:
                job_metrics[job_id] = []
            job_metrics[job_id].append(metrics)
            
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        metrics["completed_at"] = end_time
        metrics["duration_seconds"] = duration
        metrics["status"] = "failed"
        metrics["errors"].append(f"Job failed: {str(e)}")
        
        logger.error(f"Error in alert dispatch job {job_id}: {e}")
        record_incident("alert_dispatch_failure", f"Alert dispatch job failed: {str(e)}")
        
        if job_id not in job_metrics:
            job_metrics[job_id] = []
        job_metrics[job_id].append(metrics)


async def cleanup_snapshots():
    job_id = f"cleanup_snapshots_{datetime.utcnow().isoformat()}"
    start_time = datetime.utcnow()
    
    logger.info(f"Starting cleanup job {job_id}")
    
    metrics = {
        "job_id": job_id,
        "job_name": "cleanup_snapshots",
        "started_at": start_time,
        "services_processed": 0,
        "snapshots_deleted": 0,
        "snapshots_kept": 0,
        "snapshots_with_change_events": 0,
        "duplicates_removed": 0,
        "errors": []
    }
    
    try:
        async with AsyncSessionLocal() as db:
            stats = await cleanup_old_snapshots(db, keep_last_n=50)
            
            metrics["services_processed"] = stats["services_processed"]
            metrics["snapshots_deleted"] = stats["snapshots_deleted"]
            metrics["snapshots_kept"] = stats["snapshots_kept"]
            metrics["snapshots_with_change_events"] = stats["snapshots_with_change_events"]
            metrics["duplicates_removed"] = stats["duplicates_removed"]
            metrics["errors"] = stats["errors"]
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            metrics["completed_at"] = end_time
            metrics["duration_seconds"] = duration
            metrics["status"] = "completed"
            
            logger.info(
                f"Cleanup job {job_id} completed in {duration:.2f}s: "
                f"Processed {stats['services_processed']} services, "
                f"Deleted {stats['snapshots_deleted']} snapshots, "
                f"Removed {stats['duplicates_removed']} duplicates"
            )
            
            if job_id not in job_metrics:
                job_metrics[job_id] = []
            job_metrics[job_id].append(metrics)
            
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        metrics["completed_at"] = end_time
        metrics["duration_seconds"] = duration
        metrics["status"] = "failed"
        metrics["errors"].append(f"Job failed: {str(e)}")
        
        logger.error(f"Error in cleanup job {job_id}: {e}")
        
        if job_id not in job_metrics:
            job_metrics[job_id] = []
        job_metrics[job_id].append(metrics)


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
    
    scheduler.add_job(
        cleanup_snapshots,
        trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='cleanup_snapshots',
        name='Cleanup old snapshots',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

