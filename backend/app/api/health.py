from fastapi import APIRouter
from app.scheduler import scheduler, job_metrics
from app.database import AsyncSessionLocal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service
from datetime import datetime, timedelta
from typing import Dict, Any, List

router = APIRouter(prefix="/api/health", tags=["health"])
status_router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("/jobs")
async def get_jobs_health() -> Dict[str, Any]:
    jobs_status = []
    
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs_status.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })
    
    recent_metrics = {}
    for job_id, metrics_list in job_metrics.items():
        if metrics_list:
            latest = metrics_list[-1]
            recent_metrics[job_id] = {
                "status": latest.get("status", "unknown"),
                "completed_at": latest.get("completed_at").isoformat() if latest.get("completed_at") else None,
                "duration_seconds": latest.get("duration_seconds"),
                "error_count": latest.get("error_count", 0),
                "success_count": latest.get("success_count", 0)
            }
    
    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs_status,
        "recent_metrics": recent_metrics
    }


from app.scheduler import incident_history


@status_router.get("")
async def get_public_status() -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count(Service.id), func.max(Service.last_checked_at))
            .where(Service.is_active == True)
        )
        row = result.first()
        total_services = row[0] or 0
        last_check = row[1]
        
        last_24h = datetime.utcnow() - timedelta(hours=24)
        result = await db.execute(
            select(func.count(Service.id))
            .where(Service.is_active == True)
            .where(Service.last_checked_at >= last_24h)
        )
        recently_checked = result.scalar() or 0
        
        success_rate = 1.0
        if total_services > 0:
            success_rate = recently_checked / total_services
        
        uptime_percentage = 99.9
        if scheduler.running:
            fetch_job_metrics = [
                m for job_id, metrics_list in job_metrics.items()
                if "fetch_service_pages" in job_id and metrics_list
                for m in metrics_list[-10:]
            ]
            if fetch_job_metrics:
                successful = sum(1 for m in fetch_job_metrics if m.get("status") == "completed")
                total = len(fetch_job_metrics)
                if total > 0:
                    uptime_percentage = (successful / total) * 100
        
        recent_incidents = [
            inc for inc in incident_history
            if (datetime.utcnow() - datetime.fromisoformat(inc["timestamp"])).total_seconds() < 86400 * 7
        ][-10:]
        
        return {
            "status": "operational" if uptime_percentage >= 99.0 else "degraded",
            "uptime_percentage": round(uptime_percentage, 2),
            "last_check": last_check.isoformat() if last_check else None,
            "total_services": total_services,
            "recently_checked_24h": recently_checked,
            "success_rate_24h": round(success_rate * 100, 2),
            "scheduler_running": scheduler.running,
            "incidents": recent_incidents,
            "updated_at": datetime.utcnow().isoformat()
        }

