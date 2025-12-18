import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import uuid4
from app.models.service import Service, CheckFrequency
from app.models.user import User


@pytest.mark.performance
@pytest.mark.asyncio
async def test_query_with_index_on_user_id(db_session: AsyncSession, test_user):
    for i in range(50):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    start_time = time.time()
    result = await db_session.execute(
        select(Service).where(Service.user_id == test_user.id)
    )
    services = result.scalars().all()
    elapsed = time.time() - start_time
    
    assert len(services) == 50
    assert elapsed < 0.1


@pytest.mark.performance
@pytest.mark.asyncio
async def test_count_query_performance(db_session: AsyncSession, test_user):
    for i in range(100):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    start_time = time.time()
    result = await db_session.execute(
        select(func.count(Service.id)).where(Service.user_id == test_user.id)
    )
    count = result.scalar()
    elapsed = time.time() - start_time
    
    assert count == 100
    assert elapsed < 0.1


@pytest.mark.performance
@pytest.mark.asyncio
async def test_join_query_performance(db_session: AsyncSession, test_user):
    from app.models.snapshot import Snapshot
    
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
    
    for i in range(50):
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
    result = await db_session.execute(
        select(Service, Snapshot)
        .join(Snapshot, Service.id == Snapshot.service_id)
        .where(Service.user_id == test_user.id)
        .limit(10)
    )
    rows = result.all()
    elapsed = time.time() - start_time
    
    assert len(rows) == 10
    assert elapsed < 0.2

