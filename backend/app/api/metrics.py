from fastapi import APIRouter
from app.scheduler import job_metrics
from typing import Dict, Any, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
async def get_metrics() -> Dict[str, Any]:
    all_metrics = {}
    
    for job_id, metrics_list in job_metrics.items():
        if not metrics_list:
            continue
        
        recent_metrics = [m for m in metrics_list if m.get("completed_at") and 
                         (datetime.utcnow() - m["completed_at"]).total_seconds() < 86400]
        
        if not recent_metrics:
            continue
        
        total_runs = len(recent_metrics)
        successful_runs = sum(1 for m in recent_metrics if m.get("status") == "completed")
        failed_runs = sum(1 for m in recent_metrics if m.get("status") == "failed")
        avg_duration = sum(m.get("duration_seconds", 0) for m in recent_metrics) / total_runs if total_runs > 0 else 0
        total_errors = sum(m.get("error_count", 0) for m in recent_metrics)
        total_successes = sum(m.get("success_count", 0) for m in recent_metrics)
        
        all_metrics[job_id] = {
            "total_runs_24h": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
            "avg_duration_seconds": round(avg_duration, 2),
            "total_errors": total_errors,
            "total_successes": total_successes,
            "latest_status": recent_metrics[-1].get("status", "unknown"),
            "latest_completed_at": recent_metrics[-1].get("completed_at").isoformat() if recent_metrics[-1].get("completed_at") else None
        }
    
    return {
        "jobs": all_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }

