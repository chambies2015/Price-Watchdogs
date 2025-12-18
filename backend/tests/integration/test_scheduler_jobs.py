import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service, CheckFrequency
from app.models.snapshot import Snapshot
from app.models.user import User
from app.models.change_event import ChangeEvent, ChangeType
from app.scheduler import fetch_service_pages, cleanup_snapshots, process_service_with_retry
from app.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_process_service_with_retry_success(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=None
    )
    db_session.add(service)
    await db_session.commit()
    
    with patch('app.scheduler.create_snapshot') as mock_create, \
         patch('app.scheduler.process_new_snapshot') as mock_process:
        
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()
        mock_create.return_value = mock_snapshot
        mock_process.return_value = None
        
        success, status = await process_service_with_retry(db_session, service, max_retries=3)
        
        assert success is True
        assert status == "success"
        mock_create.assert_called_once()
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_process_service_with_retry_skipped_not_due(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(hours=12)
    )
    db_session.add(service)
    await db_session.commit()
    
    success, status = await process_service_with_retry(db_session, service, max_retries=3)
    
    assert success is True
    assert status == "skipped_not_due"


@pytest.mark.asyncio
async def test_process_service_with_retry_failure_retries(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=None
    )
    db_session.add(service)
    await db_session.commit()
    
    with patch('app.scheduler.create_snapshot') as mock_create:
        mock_create.side_effect = Exception("Network error")
        
        success, status = await process_service_with_retry(db_session, service, max_retries=3)
        
        assert success is False
        assert "Network error" in status
        assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_fetch_service_pages_batch_processing(db_session: AsyncSession, test_user):
    from app.database import AsyncSessionLocal
    from tests.conftest import TestSessionLocal
    
    services = []
    for i in range(12):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True,
            last_checked_at=None
        )
        services.append(service)
        db_session.add(service)
    
    await db_session.commit()
    
    with patch('app.scheduler.AsyncSessionLocal', TestSessionLocal), \
         patch('app.scheduler.create_snapshot') as mock_create, \
         patch('app.scheduler.process_new_snapshot') as mock_process:
        
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()
        mock_create.return_value = mock_snapshot
        mock_process.return_value = None
        
        await fetch_service_pages()
        
        assert mock_create.call_count == 12


@pytest.mark.asyncio
async def test_fetch_service_pages_metrics_tracking(db_session: AsyncSession, test_user):
    from app.database import engine, Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=None
    )
    db_session.add(service)
    await db_session.commit()
    
    with patch('app.scheduler.create_snapshot') as mock_create, \
         patch('app.scheduler.process_new_snapshot') as mock_process:
        
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()
        mock_create.return_value = mock_snapshot
        mock_process.return_value = None
        
        await fetch_service_pages()
        
        from app.scheduler import job_metrics
        
        assert len(job_metrics) > 0
        latest_job = list(job_metrics.values())[-1][0]
        assert latest_job["job_name"] == "fetch_service_pages"
        assert latest_job["status"] == "completed"
        assert "services_processed" in latest_job
        assert "success_count" in latest_job


@pytest.mark.asyncio
async def test_cleanup_snapshots_job(db_session: AsyncSession, test_user):
    from app.database import AsyncSessionLocal
    from tests.conftest import TestSessionLocal
    
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(service)
    await db_session.commit()
    
    for i in range(60):
        snapshot = Snapshot(
            id=uuid4(),
            service_id=service.id,
            raw_html_hash=f"raw_hash_{i}",
            normalized_content_hash=f"normalized_hash_{i}",
            normalized_content=f"Content {i}",
            created_at=datetime.utcnow() - timedelta(hours=60-i)
        )
        db_session.add(snapshot)
    
    await db_session.commit()
    
    with patch('app.scheduler.AsyncSessionLocal', TestSessionLocal):
        await cleanup_snapshots()
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.service_id == service.id)
    )
    remaining_snapshots = result.scalars().all()
    
    assert len(remaining_snapshots) == 50


@pytest.mark.asyncio
async def test_cleanup_snapshots_preserves_change_event_snapshots(db_session: AsyncSession, test_user):
    from app.database import engine, Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(service)
    await db_session.commit()
    
    old_snapshot = Snapshot(
        id=uuid4(),
        service_id=service.id,
        raw_html_hash="old_raw",
        normalized_content_hash="old_normalized",
        normalized_content="Old content",
        created_at=datetime.utcnow() - timedelta(days=100)
    )
    new_snapshot = Snapshot(
        id=uuid4(),
        service_id=service.id,
        raw_html_hash="new_raw",
        normalized_content_hash="new_normalized",
        normalized_content="New content",
        created_at=datetime.utcnow() - timedelta(days=90)
    )
    db_session.add(old_snapshot)
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = ChangeEvent(
        id=uuid4(),
        service_id=service.id,
        old_snapshot_id=old_snapshot.id,
        new_snapshot_id=new_snapshot.id,
        change_type=ChangeType.price_increase,
        summary="Price increased",
        confidence_score=0.9
    )
    db_session.add(change_event)
    
    for i in range(60):
        snapshot = Snapshot(
            id=uuid4(),
            service_id=service.id,
            raw_html_hash=f"raw_hash_{i}",
            normalized_content_hash=f"normalized_hash_{i}",
            normalized_content=f"Content {i}",
            created_at=datetime.utcnow() - timedelta(hours=60-i)
        )
        db_session.add(snapshot)
    
    await db_session.commit()
    
    await cleanup_snapshots()
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.id == old_snapshot.id)
    )
    assert result.scalar_one_or_none() is not None
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.id == new_snapshot.id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_cleanup_snapshots_metrics_tracking(db_session: AsyncSession, test_user):
    from app.database import engine, Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(service)
    await db_session.commit()
    
    for i in range(60):
        snapshot = Snapshot(
            id=uuid4(),
            service_id=service.id,
            raw_html_hash=f"raw_hash_{i}",
            normalized_content_hash=f"normalized_hash_{i}",
            normalized_content=f"Content {i}",
            created_at=datetime.utcnow() - timedelta(hours=60-i)
        )
        db_session.add(snapshot)
    
    await db_session.commit()
    
    await cleanup_snapshots()
    
    from app.scheduler import job_metrics
    
    assert len(job_metrics) > 0
    cleanup_jobs = [
        job for jobs in job_metrics.values()
        for job in jobs
        if job["job_name"] == "cleanup_snapshots"
    ]
    
    assert len(cleanup_jobs) > 0
    latest_cleanup = cleanup_jobs[-1]
    assert latest_cleanup["status"] == "completed"
    assert "snapshots_deleted" in latest_cleanup
    assert "services_processed" in latest_cleanup

