import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "password123"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_duplicate_email_registration(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    
    response = await client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    
    assert response.status_code == 400
    assert "unable to register" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_registration_requires_strong_password(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "weakpass@example.com", "password": "password"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_user_login(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "logintest@example.com", "password": "password123"}
    )
    
    response = await client.post(
        "/api/auth/login",
        json={"email": "logintest@example.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "authtest@example.com"


@pytest.mark.asyncio
async def test_get_current_user_no_auth(client: AsyncClient):
    response = await client.get("/api/auth/me")
    
    assert response.status_code == 403

