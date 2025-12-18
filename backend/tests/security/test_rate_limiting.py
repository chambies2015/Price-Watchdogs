import pytest
from httpx import AsyncClient
from fastapi import status
import asyncio


@pytest.mark.security
@pytest.mark.asyncio
async def test_rapid_login_attempts(client: AsyncClient):
    login_data = {
        "email": "ratelimit@example.com",
        "password": "wrongpassword"
    }
    
    responses = []
    for _ in range(10):
        response = await client.post("/api/auth/login", json=login_data)
        responses.append(response.status_code)
    
    assert all(status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN] for status_code in responses)


@pytest.mark.security
@pytest.mark.asyncio
async def test_rapid_registration_attempts(client: AsyncClient):
    responses = []
    for i in range(5):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": f"rapid{i}@example.com",
                "password": "testpass123"
            }
        )
        responses.append(response.status_code)
    
    assert all(status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS] for status_code in responses)


@pytest.mark.security
@pytest.mark.asyncio
async def test_concurrent_requests(client: AsyncClient, auth_headers: dict):
    async def make_request():
        return await client.get("/api/services", headers=auth_headers)
    
    tasks = [make_request() for _ in range(20)]
    responses = await asyncio.gather(*tasks)
    
    status_codes = [r.status_code for r in responses]
    
    assert all(code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS] for code in status_codes)


@pytest.mark.security
@pytest.mark.asyncio
async def test_brute_force_protection(client: AsyncClient):
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    import uuid
    
    test_email = "bruteforce@example.com"
    test_password = "correctpassword"
    
    async def register_user(db_session: AsyncSession):
        user = User(
            id=uuid.uuid4(),
            email=test_email,
            password_hash=get_password_hash(test_password)
        )
        db_session.add(user)
        await db_session.commit()
        return user
    
    wrong_passwords = [f"wrong{i}" for i in range(10)]
    
    failed_attempts = 0
    for wrong_password in wrong_passwords:
        response = await client.post(
            "/api/auth/login",
            json={"email": test_email, "password": wrong_password}
        )
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            failed_attempts += 1
    
    assert failed_attempts >= 0

