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
async def test_service_detail_with_snapshots(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
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
    
    result = await db_session.execute(
        select(Service).where(Service.id == uuid.UUID(service_id))
    )
    service = result.scalar_one()
    
    snapshot = Snapshot(
        id=uuid.uuid4(),
        service_id=service.id,
        raw_html_hash=generate_hash("Test content"),
        normalized_content_hash=generate_hash("Test content"),
        normalized_content="Test content"
    )
    db_session.add(snapshot)
    await db_session.commit()
    
    response = await client.get(
        f"/api/services/{service_id}/snapshots",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    snapshots = response.json()
    assert isinstance(snapshots, list)
    assert len(snapshots) >= 1


@pytest.mark.asyncio
async def test_service_detail_with_change_history(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
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
    
    result = await db_session.execute(
        select(Service).where(Service.id == uuid.UUID(service_id))
    )
    service = result.scalar_one()
    
    old_content = "Basic: $10"
    new_content = "Basic: $15"
    
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
        f"/api/services/{service_id}/changes",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    changes = response.json()
    assert isinstance(changes, list)
    assert len(changes) >= 1


@pytest.mark.asyncio
async def test_service_detail_with_alert_settings(client: AsyncClient, auth_headers: dict):
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
    
    response = await client.get(
        f"/api/services/{service_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "alerts_enabled" in data
    assert "alert_confidence_threshold" in data
    assert data["alerts_enabled"] is True
    assert data["alert_confidence_threshold"] == 0.6

