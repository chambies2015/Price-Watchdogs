import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.models.service import Service
from app.models.change_event import ChangeEvent, ChangeType
from app.models.snapshot import Snapshot
from app.services.processor import generate_hash
from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "total_services" in data
    assert "active_services" in data
    assert "recent_changes_count" in data
    assert isinstance(data["services"], list)
    assert isinstance(data["total_services"], int)
    assert isinstance(data["active_services"], int)
    assert isinstance(data["recent_changes_count"], int)
    if data["services"]:
        sample = data["services"][0]
        assert "check_frequency" in sample
        assert "next_check_at" in sample


@pytest.mark.asyncio
async def test_dashboard_summary_with_changes(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    result = await db_session.execute(
        select(User).limit(1)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return
    
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
    
    old_content = "Basic Plan: $10"
    new_content = "Basic Plan: $15"
    
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
    
    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["recent_changes_count"] >= 1
    
    service_summary = next((s for s in data["services"] if s["id"] == str(service.id)), None)
    assert service_summary is not None
    assert service_summary["last_change_event"] is not None
    assert service_summary["change_count"] >= 1
    assert "check_frequency" in service_summary
    assert "next_check_at" in service_summary


@pytest.mark.asyncio
async def test_dashboard_summary_last_check_status(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from datetime import datetime
    
    result = await db_session.execute(
        select(User).limit(1)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return
    
    service = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Service",
        url="https://example.com/pricing",
        last_checked_at=datetime.utcnow()
    )
    db_session.add(service)
    await db_session.commit()
    
    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    service_summary = next((s for s in data["services"] if s["id"] == str(service.id)), None)
    assert service_summary is not None
    assert service_summary["last_checked_at"] is not None
    assert service_summary["next_check_at"] is not None


@pytest.mark.asyncio
async def test_dashboard_summary_with_filters(client: AsyncClient, auth_headers: dict):
    tag_response = await client.post(
        "/api/tags",
        json={"name": "Test Tag", "color": "#ff0000"},
        headers=auth_headers
    )
    tag_id = tag_response.json()["id"]
    
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Tagged Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily",
            "tag_ids": [tag_id]
        },
        headers=auth_headers
    )
    
    await client.post(
        "/api/services",
        json={
            "name": "Untagged Service",
            "url": "https://example.com/pricing2",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    response = await client.get(
        f"/api/dashboard/summary?tags={tag_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["services"]) == 1
    assert data["services"][0]["name"] == "Tagged Service"


@pytest.mark.asyncio
async def test_dashboard_summary_with_active_filter(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/services",
        json={
            "name": "Active Service",
            "url": "https://example.com/pricing1",
            "check_frequency": "daily",
            "is_active": True
        },
        headers=auth_headers
    )
    
    await client.post(
        "/api/services",
        json={
            "name": "Inactive Service",
            "url": "https://example.com/pricing2",
            "check_frequency": "daily",
            "is_active": False
        },
        headers=auth_headers
    )
    
    response = await client.get(
        "/api/dashboard/summary?is_active=true",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(s["is_active"] is True for s in data["services"])


@pytest.mark.asyncio
async def test_dashboard_summary_with_sorting(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/services",
        json={
            "name": "Zebra Service",
            "url": "https://example.com/pricing1",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    await client.post(
        "/api/services",
        json={
            "name": "Alpha Service",
            "url": "https://example.com/pricing2",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    response = await client.get(
        "/api/dashboard/summary?sort_by=name&sort_order=asc",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    if len(data["services"]) >= 2:
        names = [s["name"] for s in data["services"]]
        assert names == sorted(names)

