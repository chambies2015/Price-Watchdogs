import pytest
import asyncio
from httpx import AsyncClient
from fastapi import status
import time


@pytest.mark.load
@pytest.mark.asyncio
async def test_health_endpoint_performance(client: AsyncClient):
    start_time = time.time()
    response = await client.get("/health")
    duration = time.time() - start_time
    
    assert response.status_code == status.HTTP_200_OK
    assert duration < 0.1, f"Health endpoint should respond in <100ms, took {duration:.3f}s"


@pytest.mark.load
@pytest.mark.asyncio
async def test_concurrent_health_requests(client: AsyncClient):
    async def make_request():
        return await client.get("/health")
    
    start_time = time.time()
    tasks = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    assert all(r.status_code == status.HTTP_200_OK for r in responses)
    assert duration < 1.0, f"10 concurrent requests should complete in <1s, took {duration:.3f}s"


@pytest.mark.load
@pytest.mark.asyncio
async def test_metrics_endpoint_performance(client: AsyncClient):
    start_time = time.time()
    response = await client.get("/api/metrics")
    duration = time.time() - start_time
    
    assert response.status_code == status.HTTP_200_OK
    assert duration < 0.5, f"Metrics endpoint should respond in <500ms, took {duration:.3f}s"


@pytest.mark.load
@pytest.mark.asyncio
async def test_jobs_health_endpoint_performance(client: AsyncClient):
    start_time = time.time()
    response = await client.get("/api/health/jobs")
    duration = time.time() - start_time
    
    assert response.status_code == status.HTTP_200_OK
    assert duration < 0.5, f"Jobs health endpoint should respond in <500ms, took {duration:.3f}s"


@pytest.mark.load
@pytest.mark.asyncio
async def test_auth_endpoint_under_load(setup_database):
    from httpx import AsyncClient
    from app.main import app
    from app.database import get_db, Base
    from tests.conftest import TestSessionLocal, engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            async def attempt_login():
                return await client.post("/api/auth/login", json={
                    "email": "loadtest@example.com",
                    "password": "wrongpassword"
                })
            
            start_time = time.time()
            tasks = [attempt_login() for _ in range(20)]
            responses = await asyncio.gather(*tasks)
            duration = time.time() - start_time
            
            assert all(r.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS] for r in responses)
            assert duration < 2.0, f"20 login attempts should complete in <2s, took {duration:.3f}s"
    finally:
        app.dependency_overrides.clear()

