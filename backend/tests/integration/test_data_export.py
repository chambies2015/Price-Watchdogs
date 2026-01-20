import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.models.change_event import ChangeType


@pytest.mark.asyncio
async def test_export_service_changes_csv(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.get(
        f"/api/exports/services/{service_id}/changes.csv",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert "attachment" in response.headers["Content-Disposition"]
    
    content = response.text
    assert "id,service_id,service_name,change_type" in content


@pytest.mark.asyncio
async def test_export_service_changes_json(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.get(
        f"/api/exports/services/{service_id}/changes.json",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_export_service_changes_with_limit(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.get(
        f"/api/exports/services/{service_id}/changes.json?limit=5",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_export_service_changes_with_date_filter(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    end_date = datetime.utcnow().isoformat()
    
    response = await client.get(
        f"/api/exports/services/{service_id}/changes.json?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_export_service_snapshots_csv(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.get(
        f"/api/exports/services/{service_id}/snapshots.csv",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    content = response.text
    assert "id,service_id,service_name,created_at" in content


@pytest.mark.asyncio
async def test_export_service_snapshots_json(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.get(
        f"/api/exports/services/{service_id}/snapshots.json",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_export_all_changes_csv(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/services",
        json={
            "name": "Service 1",
            "url": "https://example.com/pricing1",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    await client.post(
        "/api/services",
        json={
            "name": "Service 2",
            "url": "https://example.com/pricing2",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    response = await client.get(
        "/api/exports/all/changes.csv",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    content = response.text
    assert "id,service_id,service_name,change_type" in content


@pytest.mark.asyncio
async def test_export_all_changes_json(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/services",
        json={
            "name": "Service 1",
            "url": "https://example.com/pricing1",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    response = await client.get(
        "/api/exports/all/changes.json",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_export_service_changes_not_found(client: AsyncClient, auth_headers: dict):
    import uuid
    fake_id = str(uuid.uuid4())
    
    response = await client.get(
        f"/api/exports/services/{fake_id}/changes.csv",
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_service_changes_invalid_date_format(client: AsyncClient, auth_headers: dict):
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.get(
        f"/api/exports/services/{service_id}/changes.json?start_date=invalid-date",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "date" in response.json()["detail"].lower()
