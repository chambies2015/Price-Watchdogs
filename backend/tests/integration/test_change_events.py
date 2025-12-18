import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.models.service import Service
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent, ChangeType
from app.services.diff_service import compare_snapshots, process_new_snapshot
from app.services.processor import generate_hash


@pytest.mark.asyncio
async def test_compare_snapshots_with_change(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Basic Plan: $10 per month\nPro Plan: $20 per month"
    new_content = "Basic Plan: $15 per month\nPro Plan: $25 per month"
    
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
    assert change_event.service_id == service.id
    assert change_event.old_snapshot_id == old_snapshot.id
    assert change_event.new_snapshot_id == new_snapshot.id
    assert change_event.change_type == ChangeType.price_increase
    assert change_event.confidence_score >= 0.6
    assert "increase" in change_event.summary.lower()


@pytest.mark.asyncio
async def test_compare_snapshots_no_change(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    content = "Basic Plan: $10 per month"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(content),
        normalized_content_hash=generate_hash(content),
        normalized_content=content
    )
    db_session.add(old_snapshot)
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(content),
        normalized_content_hash=generate_hash(content),
        normalized_content=content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await compare_snapshots(db_session, old_snapshot, new_snapshot)
    
    assert change_event is None


@pytest.mark.asyncio
async def test_compare_snapshots_low_confidence(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Updated: January 1, 2024"
    new_content = "Updated: January 2, 2024"
    
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
    
    assert change_event is None


@pytest.mark.asyncio
async def test_process_new_snapshot_creates_change_event(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Free Plan: $0\nPro Plan: $20"
    new_content = "Pro Plan: $20\nEnterprise Plan: $50"
    
    old_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(old_content),
        normalized_content_hash=generate_hash(old_content),
        normalized_content=old_content
    )
    db_session.add(old_snapshot)
    await db_session.commit()
    
    new_snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(new_content),
        normalized_content_hash=generate_hash(new_content),
        normalized_content=new_content
    )
    db_session.add(new_snapshot)
    await db_session.commit()
    
    change_event = await process_new_snapshot(db_session, new_snapshot)
    
    assert change_event is not None
    assert change_event.change_type == ChangeType.free_tier_removed
    assert change_event.confidence_score >= 0.8


@pytest.mark.asyncio
async def test_process_new_snapshot_no_previous_snapshot(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    content = "Basic Plan: $10"
    
    snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(content),
        normalized_content_hash=generate_hash(content),
        normalized_content=content
    )
    db_session.add(snapshot)
    await db_session.commit()
    
    change_event = await process_new_snapshot(db_session, snapshot)
    
    assert change_event is None


@pytest.mark.asyncio
async def test_change_event_storage_and_retrieval(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
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
        select(ChangeEvent).where(ChangeEvent.id == change_event.id)
    )
    retrieved_event = result.scalar_one()
    
    assert retrieved_event.id == change_event.id
    assert retrieved_event.service_id == service.id
    assert retrieved_event.change_type == ChangeType.price_increase


@pytest.mark.asyncio
async def test_multiple_change_events_for_service(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    snapshot1_content = "Price: $10"
    snapshot2_content = "Price: $15"
    snapshot3_content = "Price: $20"
    
    snapshot1 = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(snapshot1_content),
        normalized_content_hash=generate_hash(snapshot1_content),
        normalized_content=snapshot1_content
    )
    db_session.add(snapshot1)
    await db_session.commit()
    
    snapshot2 = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(snapshot2_content),
        normalized_content_hash=generate_hash(snapshot2_content),
        normalized_content=snapshot2_content
    )
    db_session.add(snapshot2)
    await db_session.commit()
    
    change1 = await compare_snapshots(db_session, snapshot1, snapshot2)
    assert change1 is not None
    
    snapshot3 = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash(snapshot3_content),
        normalized_content_hash=generate_hash(snapshot3_content),
        normalized_content=snapshot3_content
    )
    db_session.add(snapshot3)
    await db_session.commit()
    
    change2 = await compare_snapshots(db_session, snapshot2, snapshot3)
    assert change2 is not None
    
    result = await db_session.execute(
        select(ChangeEvent)
        .where(ChangeEvent.service_id == service.id)
        .order_by(ChangeEvent.created_at.desc())
    )
    events = result.scalars().all()
    
    assert len(events) == 2
    assert all(e.change_type == ChangeType.price_increase for e in events)


@pytest.mark.asyncio
async def test_list_service_changes_api(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    result = await db_session.execute(
        select(Service).limit(1)
    )
    service = result.scalar_one_or_none()
    
    if not service:
        return
    
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
    
    response = await client.get(
        f"/api/services/{service.id}/changes",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    changes = response.json()
    assert isinstance(changes, list)
    assert len(changes) >= 1


@pytest.mark.asyncio
async def test_get_change_event_api(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    result = await db_session.execute(
        select(Service).limit(1)
    )
    service = result.scalar_one_or_none()
    
    if not service:
        return
    
    old_content = "Pro: $20"
    new_content = "Pro: $30"
    
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
    
    response = await client.get(
        f"/api/services/changes/{change_event.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    change = response.json()
    assert change["id"] == str(change_event.id)
    assert change["change_type"] == ChangeType.price_increase.value


@pytest.mark.asyncio
async def test_noise_filtering(db_session: AsyncSession, test_user):
    service = Service(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test Service",
        url="https://example.com/pricing"
    )
    db_session.add(service)
    await db_session.commit()
    
    old_content = "Pricing updated: 2024-01-01 10:30:45\nBasic Plan: $10"
    new_content = "Pricing updated: 2024-01-02 11:45:30\nBasic Plan: $10"
    
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
    
    assert change_event is None

