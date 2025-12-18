import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service, CheckFrequency
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent, ChangeType
from app.models.user import User
from app.services.cleanup_service import cleanup_service_snapshots, cleanup_old_snapshots


@pytest.mark.asyncio
async def test_cleanup_service_snapshots_keeps_last_n(db_session: AsyncSession, test_user):
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
    
    stats = await cleanup_service_snapshots(db_session, service.id, keep_last_n=50)
    
    assert stats["deleted"] == 10
    assert stats["kept"] >= 50
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.service_id == service.id)
    )
    remaining_snapshots = result.scalars().all()
    assert len(remaining_snapshots) == 50


@pytest.mark.asyncio
async def test_cleanup_service_snapshots_keeps_change_event_snapshots(db_session: AsyncSession, test_user):
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
    
    stats = await cleanup_service_snapshots(db_session, service.id, keep_last_n=50)
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.id == old_snapshot.id)
    )
    assert result.scalar_one_or_none() is not None
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.id == new_snapshot.id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_cleanup_service_snapshots_deduplicates(db_session: AsyncSession, test_user):
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
    
    same_hash = "duplicate_hash"
    
    for i in range(5):
        snapshot = Snapshot(
            id=uuid4(),
            service_id=service.id,
            raw_html_hash=f"raw_{i}",
            normalized_content_hash=same_hash,
            normalized_content="Same content",
            created_at=datetime.utcnow() - timedelta(hours=5-i)
        )
        db_session.add(snapshot)
    
    await db_session.commit()
    
    stats = await cleanup_service_snapshots(db_session, service.id, keep_last_n=50)
    
    assert stats["duplicates_removed"] == 4
    
    result = await db_session.execute(
        select(Snapshot).where(Snapshot.service_id == service.id)
    )
    remaining_snapshots = result.scalars().all()
    assert len(remaining_snapshots) == 1


@pytest.mark.asyncio
async def test_cleanup_service_snapshots_no_snapshots(db_session: AsyncSession, test_user):
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
    
    stats = await cleanup_service_snapshots(db_session, service.id, keep_last_n=50)
    
    assert stats["deleted"] == 0
    assert stats["kept"] == 0
    assert stats["duplicates_removed"] == 0


@pytest.mark.asyncio
async def test_cleanup_old_snapshots_multiple_services(db_session: AsyncSession, test_user):
    service1 = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Service 1",
        url="https://example1.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    service2 = Service(
        id=uuid4(),
        user_id=test_user.id,
        name="Service 2",
        url="https://example2.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(service1)
    db_session.add(service2)
    await db_session.commit()
    
    for i in range(60):
        snapshot1 = Snapshot(
            id=uuid4(),
            service_id=service1.id,
            raw_html_hash=f"raw1_{i}",
            normalized_content_hash=f"norm1_{i}",
            normalized_content=f"Content 1-{i}",
            created_at=datetime.utcnow() - timedelta(hours=60-i)
        )
        snapshot2 = Snapshot(
            id=uuid4(),
            service_id=service2.id,
            raw_html_hash=f"raw2_{i}",
            normalized_content_hash=f"norm2_{i}",
            normalized_content=f"Content 2-{i}",
            created_at=datetime.utcnow() - timedelta(hours=60-i)
        )
        db_session.add(snapshot1)
        db_session.add(snapshot2)
    
    await db_session.commit()
    
    stats = await cleanup_old_snapshots(db_session, keep_last_n=50)
    
    assert stats["services_processed"] == 2
    assert stats["snapshots_deleted"] == 20
    assert stats["snapshots_kept"] >= 100

