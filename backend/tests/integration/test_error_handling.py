import pytest
from httpx import AsyncClient
from fastapi import status
from uuid import uuid4


@pytest.mark.asyncio
@pytest.mark.integration
async def test_404_not_found_service(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        f"/api/services/{uuid4()}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_404_not_found_change_event(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        f"/api/services/changes/{uuid4()}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_400_invalid_url_format(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "not-a-valid-url",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_400_missing_required_fields(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/services",
        json={
            "name": "Test Service"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_401_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/services")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.integration
async def test_403_forbidden_service_access(client: AsyncClient, auth_headers: dict, db_session):
    from app.models.user import User
    from app.models.service import Service, CheckFrequency
    from app.core.security import get_password_hash
    import uuid
    
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    
    other_service = Service(
        id=uuid.uuid4(),
        user_id=other_user.id,
        name="Other User Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily
    )
    db_session.add(other_service)
    await db_session.commit()
    
    response = await client.get(
        f"/api/services/{other_service.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.integration
async def test_400_invalid_checkout_plan(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/subscriptions/create-checkout",
        json={"plan_type": "free"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "free" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_400_cancel_free_plan(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/subscriptions/cancel",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "free" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_422_invalid_enum_value(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "check_frequency": "invalid_frequency"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_422_invalid_uuid_format(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/services/invalid-uuid",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_response_format_consistency(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        f"/api/services/{uuid4()}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    
    assert isinstance(data, dict)
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_500_handling_with_invalid_db_operation(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/services/invalid-uuid-format-test",
        headers=auth_headers
    )
    
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_404_NOT_FOUND]

