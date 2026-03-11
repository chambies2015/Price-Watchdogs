import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_service(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/services",
        json={
            "name": "Stripe Pricing",
            "url": "https://stripe.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Stripe Pricing"
    assert data["url"] == "https://stripe.com/pricing"
    assert data["check_frequency"] == "daily"
    assert data["alerts_enabled"] is True
    assert data["alert_confidence_threshold"] == 0.6
    assert "id" in data


@pytest.mark.asyncio
async def test_create_service_invalid_url(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/services",
        json={
            "name": "Invalid Service",
            "url": "not-a-valid-url",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_services(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/services",
        json={
            "name": "Service 1",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    response = await client.get("/api/services", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_service(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = create_response.json()["id"]
    
    response = await client.get(f"/api/services/{service_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == service_id
    assert data["name"] == "Test Service"


@pytest.mark.asyncio
async def test_update_service(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/services",
        json={
            "name": "Original Name",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = create_response.json()["id"]
    
    response = await client.put(
        f"/api/services/{service_id}",
        json={
            "name": "Updated Name",
            "check_frequency": "weekly",
            "is_active": False
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["check_frequency"] == "weekly"
    assert data["is_active"] is False
    assert "alerts_enabled" in data
    assert "alert_confidence_threshold" in data


@pytest.mark.asyncio
async def test_delete_service(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/services",
        json={
            "name": "To Delete",
            "url": "https://example.com/pricing",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    service_id = create_response.json()["id"]
    
    response = await client.delete(f"/api/services/{service_id}", headers=auth_headers)
    
    assert response.status_code == 204
    
    get_response = await client.get(f"/api/services/{service_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_service_requires_auth(client: AsyncClient):
    response = await client.post(
        "/api/services",
        json={
            "name": "Test",
            "url": "https://example.com",
            "check_frequency": "daily"
        }
    )
    
    assert response.status_code == 401

