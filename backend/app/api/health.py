from fastapi import APIRouter
from app.scheduler import scheduler, job_metrics
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/api/health", tags=["health"])


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

