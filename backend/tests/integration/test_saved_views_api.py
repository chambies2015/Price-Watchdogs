import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_saved_view(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/saved-views",
        json={
            "name": "Active Services",
            "filter_active": True,
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Active Services"
    assert data["filter_active"] is True
    assert data["sort_by"] == "name"
    assert data["sort_order"] == "asc"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_saved_view_with_tags(client: AsyncClient, auth_headers: dict):
    tag_response = await client.post(
        "/api/tags",
        json={"name": "Important", "color": "#ff0000"},
        headers=auth_headers
    )
    tag_id = tag_response.json()["id"]
    
    response = await client.post(
        "/api/saved-views",
        json={
            "name": "Important Services",
            "filter_tags": [tag_id],
            "sort_by": "created_at",
            "sort_order": "desc"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Important Services"
    assert data["filter_tags"] == [tag_id]
    assert data["sort_by"] == "created_at"
    assert data["sort_order"] == "desc"


@pytest.mark.asyncio
async def test_create_saved_view_duplicate_name(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/saved-views",
        json={
            "name": "Duplicate",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    
    response = await client.post(
        "/api/saved-views",
        json={
            "name": "Duplicate",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_saved_views(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/saved-views",
        json={
            "name": "View 1",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    await client.post(
        "/api/saved-views",
        json={
            "name": "View 2",
            "sort_by": "created_at",
            "sort_order": "desc"
        },
        headers=auth_headers
    )
    
    response = await client.get("/api/saved-views", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    view_names = [view["name"] for view in data]
    assert "View 1" in view_names
    assert "View 2" in view_names


@pytest.mark.asyncio
async def test_get_saved_view(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/saved-views",
        json={
            "name": "Test View",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    view_id = create_response.json()["id"]
    
    response = await client.get(f"/api/saved-views/{view_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == view_id
    assert data["name"] == "Test View"


@pytest.mark.asyncio
async def test_update_saved_view(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/saved-views",
        json={
            "name": "Original",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    view_id = create_response.json()["id"]
    
    response = await client.put(
        f"/api/saved-views/{view_id}",
        json={
            "name": "Updated",
            "filter_active": True,
            "sort_by": "last_checked_at",
            "sort_order": "desc"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["filter_active"] is True
    assert data["sort_by"] == "last_checked_at"
    assert data["sort_order"] == "desc"


@pytest.mark.asyncio
async def test_delete_saved_view(client: AsyncClient, auth_headers: dict):
    create_response = await client.post(
        "/api/saved-views",
        json={
            "name": "To Delete",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    view_id = create_response.json()["id"]
    
    response = await client.delete(f"/api/saved-views/{view_id}", headers=auth_headers)
    
    assert response.status_code == 204
    
    get_response = await client.get(f"/api/saved-views/{view_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_saved_view_not_accessible_by_other_user(client: AsyncClient, auth_headers: dict, db_session):
    from app.core.security import get_password_hash, create_access_token
    from app.models.user import User
    import uuid
    
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    await db_session.commit()
    
    create_response = await client.post(
        "/api/saved-views",
        json={
            "name": "Private View",
            "sort_by": "name",
            "sort_order": "asc"
        },
        headers=auth_headers
    )
    view_id = create_response.json()["id"]
    
    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    response = await client.get(f"/api/saved-views/{view_id}", headers=other_headers)
    assert response.status_code == 404
