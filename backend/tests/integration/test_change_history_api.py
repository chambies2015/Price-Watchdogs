import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.models.service import Service
from app.models.change_event import ChangeEvent, ChangeType
from app.models.snapshot import Snapshot
from app.services.processor import generate_hash


@pytest.mark.asyncio
async def test_change_history_endpoint(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
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
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=service.id,
        old_snapshot_id=old_snapshot.id,
        new_snapshot_id=new_snapshot.id,
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.85
    )
    db_session.add(change_event)
    await db_session.commit()
    
    response = await client.get(
        f"/api/services/{service.id}/changes",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    changes = response.json()
    assert isinstance(changes, list)
    assert len(changes) >= 1
    assert changes[0]["id"] == str(change_event.id)


@pytest.mark.asyncio
async def test_change_event_detail_with_snapshots(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    result = await db_session.execute(
        select(Service).limit(1)
    )
    service = result.scalar_one_or_none()
    
    if not service:
        return
    
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
    
    change_event = ChangeEvent(
        id=uuid.uuid4(),
        service_id=service.id,
        old_snapshot_id=old_snapshot.id,
        new_snapshot_id=new_snapshot.id,
        change_type=ChangeType.price_increase,
        summary="Price increase detected",
        confidence_score=0.85
    )
    db_session.add(change_event)
    await db_session.commit()
    
    response = await client.get(
        f"/api/services/changes/{change_event.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(change_event.id)
    assert "old_snapshot" in data
    assert "new_snapshot" in data
    assert data["old_snapshot"] is not None
    assert data["new_snapshot"] is not None
    assert data["old_snapshot"]["normalized_content"] == old_content
    assert data["new_snapshot"]["normalized_content"] == new_content


@pytest.mark.asyncio
async def test_change_history_pagination(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    result = await db_session.execute(
        select(Service).limit(1)
    )
    service = result.scalar_one_or_none()
    
    if not service:
        return
    
    for i in range(5):
        old_content = f"Price: ${10 + i}"
        new_content = f"Price: ${15 + i}"
        
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
        
        change_event = ChangeEvent(
            id=uuid.uuid4(),
            service_id=service.id,
            old_snapshot_id=old_snapshot.id,
            new_snapshot_id=new_snapshot.id,
            change_type=ChangeType.price_increase,
            summary=f"Price increase {i}",
            confidence_score=0.85
        )
        db_session.add(change_event)
        await db_session.commit()
    
    response = await client.get(
        f"/api/services/{service.id}/changes?limit=3",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    changes = response.json()
    assert len(changes) <= 3

