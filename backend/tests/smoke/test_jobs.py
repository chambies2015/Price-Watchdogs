import pytest
from httpx import AsyncClient
from app.scheduler import scheduler


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_scheduler_is_running():
    assert scheduler.running, "Scheduler should be running"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_scheduler_has_jobs():
    jobs = scheduler.get_jobs()
    assert len(jobs) > 0, "Scheduler should have at least one job"
    
    job_ids = [job.id for job in jobs]
    assert "fetch_service_pages" in job_ids
    assert "dispatch_pending_alerts" in job_ids
    assert "cleanup_snapshots" in job_ids


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_jobs_health_endpoint_shows_scheduler(client: AsyncClient):
    response = await client.get("/api/health/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["scheduler_running"] is True
    assert len(data["jobs"]) > 0


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_job_schedules_are_valid():
    jobs = scheduler.get_jobs()
    for job in jobs:
        assert job.next_run_time is not None or job.trigger is not None

