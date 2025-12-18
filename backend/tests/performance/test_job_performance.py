import pytest
import time
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service, CheckFrequency
from app.models.snapshot import Snapshot
from app.services.cleanup_service import cleanup_old_snapshots
from app.scheduler import should_check_service


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cleanup_job_performance_with_many_snapshots(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(service)
    await db_session.flush()
    
    for i in range(100):
        snapshot = Snapshot(
            id=uuid4(),
            service_id=service.id,
            raw_html_hash=f"hash_{i}",
            normalized_content_hash=f"norm_hash_{i}",
            normalized_content=f"Content {i}"
        )
        db_session.add(snapshot)
    
    await db_session.commit()
    
    start_time = time.time()
    stats = await cleanup_old_snapshots(db_session, keep_last_n=50)
    elapsed = time.time() - start_time
    
    assert stats["services_processed"] == 1
    assert elapsed < 5.0


@pytest.mark.performance
@pytest.mark.asyncio
async def test_should_check_service_performance():
    from datetime import datetime, timedelta
    
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        last_checked_at=datetime.utcnow() - timedelta(hours=25)
    )
    
    iterations = 1000
    start_time = time.time()
    
    for _ in range(iterations):
        should_check_service(service)
    
    elapsed = time.time() - start_time
    
    assert elapsed < 0.1


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cleanup_job_with_multiple_services(db_session: AsyncSession, test_user):
    services = []
    for i in range(10):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
        services.append(service)
        await db_session.flush()
        
        for j in range(20):
            snapshot = Snapshot(
                id=uuid4(),
                service_id=service.id,
                raw_html_hash=f"hash_{i}_{j}",
                normalized_content_hash=f"norm_hash_{i}_{j}",
                normalized_content=f"Content {i}_{j}"
            )
            db_session.add(snapshot)
    
    await db_session.commit()
    
    start_time = time.time()
    stats = await cleanup_old_snapshots(db_session, keep_last_n=10)
    elapsed = time.time() - start_time
    
    assert stats["services_processed"] == 10
    assert elapsed < 10.0

