import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.alert import Alert
from app.models.change_event import ChangeEvent, ChangeType
from app.models.service import Service, CheckFrequency
from app.models.user import User
from app.models.snapshot import Snapshot
from app.services.processor import generate_hash
from app.services.diff_service import compare_snapshots
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_alert_creation_on_change_event(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Basic Plan: $10 per month"
    new_content = "Basic Plan: $15 per month"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(old_content),
        normalized_content_hash=generate_hash(old_content),
        normalized_content=old_content
    )
    db_session.add(old_snapshot)
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(new_content),
        normalized_content_hash=generate_hash(new_content),
        normalized_content=new_content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await compare_snapshots(db_session, old_snapshot, new_snapshot)
    assert change_event is not None
    
    result = await db_session.execute(
        select(Alert).where(Alert.change_event_id == change_event.id)
    )
    alert = result.scalar_one_or_none()
    
    assert alert is not None
    assert alert.change_event_id == change_event.id
    assert alert.user_id == test_user.id
    assert alert.sent_at is None


@pytest.mark.asyncio
async def test_alert_linking_to_change_event_and_user(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Pro Plan: $20"
    new_content = "Pro Plan: $25"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(old_content),
        normalized_content_hash=generate_hash(old_content),
        normalized_content=old_content
    )
    db_session.add(old_snapshot)
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(new_content),
        normalized_content_hash=generate_hash(new_content),
        normalized_content=new_content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await compare_snapshots(db_session, old_snapshot, new_snapshot)
    assert change_event is not None
    
    result = await db_session.execute(
        select(Alert)
        .where(Alert.change_event_id == change_event.id)
        .options(selectinload(Alert.change_event), selectinload(Alert.user))
    )
    alert = result.scalar_one_or_none()
    
    assert alert is not None
    assert alert.change_event.id == change_event.id
    assert alert.user.id == test_user.id


@pytest.mark.asyncio
@patch('app.services.email_service.send_alert_email')
async def test_email_sending_with_mock_provider(
    mock_send_email,
    db_session: AsyncSession,
    test_user
):
    mock_send_email.return_value = True
    
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Basic: $10"
    new_content = "Basic: $20"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(old_content),
        normalized_content_hash=generate_hash(old_content),
        normalized_content=old_content
    )
    db_session.add(old_snapshot)
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(new_content),
        normalized_content_hash=generate_hash(new_content),
        normalized_content=new_content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await compare_snapshots(db_session, old_snapshot, new_snapshot)
    assert change_event is not None
    
    result = await db_session.execute(
        select(Alert).where(Alert.change_event_id == change_event.id)
    )
    alert = result.scalar_one_or_none()
    assert alert is not None
    
    from app.services.email_service import send_alert_email
    from sqlalchemy.orm import selectinload
    
    await db_session.refresh(alert, ["change_event", "user"])
    await db_session.refresh(
        alert.change_event,
        ["service", "old_snapshot", "new_snapshot"]
    )
    
    success = await send_alert_email(
        alert.change_event,
        alert.change_event.service,
        alert.user,
        alert.change_event.old_snapshot,
        alert.change_event.new_snapshot
    )
    
    assert success is True
    
    alert.sent_at = datetime.utcnow()
    await db_session.commit()
    
    await db_session.refresh(alert)
    assert alert.sent_at is not None


@pytest.mark.asyncio
async def test_alert_dispatch_job_processing(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Price: $10"
    new_content = "Price: $15"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(old_content),
        normalized_content_hash=generate_hash(old_content),
        normalized_content=old_content
    )
    db_session.add(old_snapshot)
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(new_content),
        normalized_content_hash=generate_hash(new_content),
        normalized_content=new_content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await compare_snapshots(db_session, old_snapshot, new_snapshot)
    assert change_event is not None
    
    result = await db_session.execute(
        select(Alert).where(Alert.sent_at.is_(None))
    )
    pending_alerts = result.scalars().all()
    assert len(pending_alerts) >= 1


@pytest.mark.asyncio
async def test_user_alert_settings_enforcement(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing",
        alerts_enabled=False,
        alert_confidence_threshold=0.6
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Basic: $10"
    new_content = "Basic: $20"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(old_content),
        normalized_content_hash=generate_hash(old_content),
        normalized_content=old_content
    )
    db_session.add(old_snapshot)
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(new_content),
        normalized_content_hash=generate_hash(new_content),
        normalized_content=new_content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await compare_snapshots(db_session, old_snapshot, new_snapshot)
    assert change_event is not None
    
    result = await db_session.execute(
        select(Alert).where(Alert.change_event_id == change_event.id)
    )
    alert = result.scalar_one_or_none()
    
    assert alert is None


@pytest.mark.asyncio
async def test_service_update_alert_settings(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    create_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing"
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    service_id = create_response.json()["id"]
    
    update_response = await client.put(
        f"/api/services/{service_id}",
        json={
            "alerts_enabled": False,
            "alert_confidence_threshold": 0.8
        },
        headers=auth_headers
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["alerts_enabled"] is False
    assert data["alert_confidence_threshold"] == 0.8

