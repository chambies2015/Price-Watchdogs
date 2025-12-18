import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime
from app.services.alert_service import create_alert_for_change_event
from app.models.alert import Alert
from app.models.change_event import ChangeEvent, ChangeType
from app.models.service import Service, CheckFrequency
from app.models.user import User
from app.models.snapshot import Snapshot
from app.services.processor import generate_hash
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_alert_for_change_event_success(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    await db_session.commit()
    
    service = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=service.id,
        old_snapshot_id=uuid.uuid4(),
        new_snapshot_id=uuid.uuid4(),
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.85
    )
    db_session.add(change_event)
    await db_session.commit()
    
    alert = await create_alert_for_change_event(db_session, change_event)
    
    assert alert is not None
    assert alert.change_event_id == change_event.id
    assert alert.user_id == user.id
    assert alert.sent_at is None


@pytest.mark.asyncio
async def test_create_alert_alerts_disabled(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    await db_session.commit()
    
    service = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=False,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=service.id,
        old_snapshot_id=uuid.uuid4(),
        new_snapshot_id=uuid.uuid4(),
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.85
    )
    db_session.add(change_event)
    await db_session.commit()
    
    alert = await create_alert_for_change_event(db_session, change_event)
    
    assert alert is None


@pytest.mark.asyncio
async def test_create_alert_confidence_below_threshold(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    await db_session.commit()
    
    service = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.9
    )
    db_session.add(service)
    await db_session.commit()
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=service.id,
        old_snapshot_id=uuid.uuid4(),
        new_snapshot_id=uuid.uuid4(),
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.5
    )
    db_session.add(change_event)
    await db_session.commit()
    
    alert = await create_alert_for_change_event(db_session, change_event)
    
    assert alert is None


@pytest.mark.asyncio
async def test_create_alert_deduplication(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    await db_session.commit()
    
    service = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=service.id,
        old_snapshot_id=uuid.uuid4(),
        new_snapshot_id=uuid.uuid4(),
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.85
    )
    db_session.add(change_event)
    await db_session.commit()
    
    alert1 = await create_alert_for_change_event(db_session, change_event)
    assert alert1 is not None
    
    alert2 = await create_alert_for_change_event(db_session, change_event)
    assert alert2 is not None
    assert alert2.id == alert1.id


@pytest.mark.asyncio
async def test_create_alert_service_not_found(db_session: AsyncSession):
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        old_snapshot_id=uuid.uuid4(),
        new_snapshot_id=uuid.uuid4(),
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.85
    )
    db_session.add(change_event)
    await db_session.commit()
    
    alert = await create_alert_for_change_event(db_session, change_event)
    
    assert alert is None

