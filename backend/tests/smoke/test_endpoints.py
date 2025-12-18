import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_jobs_health_endpoint(client: AsyncClient):
    response = await client.get("/api/health/jobs")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "scheduler_running" in data
    assert "jobs" in data


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    response = await client.get("/api/metrics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "jobs" in data
    assert "timestamp" in data


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_auth_endpoints_exist(client: AsyncClient):
    register_response = await client.post("/api/auth/register", json={
        "email": "smoketest@example.com",
        "password": "testpass123"
    })
    assert register_response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS]
    
    login_response = await client.post("/api/auth/login", json={
        "email": "smoketest@example.com",
        "password": "testpass123"
    })
    assert login_response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS]


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_services_endpoint_requires_auth(client: AsyncClient):
    response = await client.get("/api/services")
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_subscriptions_endpoint_requires_auth(client: AsyncClient):
    response = await client.get("/api/subscriptions/current")
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

