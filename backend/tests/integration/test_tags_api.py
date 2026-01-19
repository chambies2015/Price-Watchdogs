import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tag import Tag
from app.models.service import Service


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/tags",
        json={
            "name": "Important",
            "color": "#ff0000"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Important"
    assert data["color"] == "#ff0000"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_tag_duplicate_name(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/tags",
        json={"name": "Duplicate", "color": "#0000ff"},
        headers=auth_headers
    )
    
    response = await client.post(
        "/api/tags",
        json={"name": "Duplicate", "color": "#ff0000"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/tags",
        json={"name": "Tag 1", "color": "#ff0000"},
        headers=auth_headers
    )
    await client.post(
        "/api/tags",
        json={"name": "Tag 2", "color": "#00ff00"},
        headers=auth_headers
    )
    
    response = await client.get("/api/tags", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    tag_names = [tag["name"] for tag in data]
    assert "Tag 1" in tag_names
    assert "Tag 2" in tag_names


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/tags",
        json={"name": "Original", "color": "#ff0000"},
        headers=auth_headers
    )
    tag_id = create_response.json()["id"]
    
    response = await client.put(
        f"/api/tags/{tag_id}",
        json={"name": "Updated", "color": "#00ff00"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["color"] == "#00ff00"


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/tags",
        json={"name": "To Delete", "color": "#ff0000"},
        headers=auth_headers
    )
    tag_id = create_response.json()["id"]
    
    response = await client.delete(f"/api/tags/{tag_id}", headers=auth_headers)
    
    assert response.status_code == 204
    
    get_response = await client.get(f"/api/tags/{tag_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_add_tag_to_service(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    tag_response = await client.post(
        "/api/tags",
        json={"name": "Test Tag", "color": "#ff0000"},
        headers=auth_headers
    )
    tag_id = tag_response.json()["id"]
    
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
    
    response = await client.post(
        f"/api/tags/{tag_id}/services/{service_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    get_response = await client.get(f"/api/services/{service_id}", headers=auth_headers)
    service_data = get_response.json()
    assert "tags" in service_data
    assert len(service_data["tags"]) == 1
    assert service_data["tags"][0]["id"] == tag_id


@pytest.mark.asyncio
async def test_remove_tag_from_service(client: AsyncClient, auth_headers: dict):
    tag_response = await client.post(
        "/api/tags",
        json={"name": "Test Tag", "color": "#ff0000"},
        headers=auth_headers
    )
    tag_id = tag_response.json()["id"]
    
    service_response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com/pricing",
            "check_frequency": "daily",
            "tag_ids": [tag_id]
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    response = await client.delete(
        f"/api/tags/{tag_id}/services/{service_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    get_response = await client.get(f"/api/services/{service_id}", headers=auth_headers)
    service_data = get_response.json()
    assert len(service_data["tags"]) == 0


@pytest.mark.asyncio
async def test_create_service_with_tags(client: AsyncClient, auth_headers: dict):
    tag_response = await client.post(
        "/api/tags",
        json={"name": "Important", "color": "#ff0000"},
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
    
    assert service_response.status_code == 201
    service_data = service_response.json()
    assert len(service_data["tags"]) == 1
    assert service_data["tags"][0]["id"] == tag_id


@pytest.mark.asyncio
async def test_filter_services_by_tags(client: AsyncClient, auth_headers: dict):
    tag1_response = await client.post(
        "/api/tags",
        json={"name": "Tag 1", "color": "#ff0000"},
        headers=auth_headers
    )
    tag1_id = tag1_response.json()["id"]
    
    tag2_response = await client.post(
        "/api/tags",
        json={"name": "Tag 2", "color": "#00ff00"},
        headers=auth_headers
    )
    tag2_id = tag2_response.json()["id"]
    
    await client.post(
        "/api/services",
        json={
            "name": "Service 1",
            "url": "https://example.com/pricing1",
            "check_frequency": "daily",
            "tag_ids": [tag1_id]
        },
        headers=auth_headers
    )
    
    await client.post(
        "/api/services",
        json={
            "name": "Service 2",
            "url": "https://example.com/pricing2",
            "check_frequency": "daily",
            "tag_ids": [tag2_id]
        },
        headers=auth_headers
    )
    
    response = await client.get(
        f"/api/services?tags={tag1_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    services = response.json()
    assert len(services) == 1
    assert services[0]["name"] == "Service 1"
