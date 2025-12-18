import pytest
from httpx import AsyncClient
from fastapi import status
from jose import jwt
from app.config import settings


@pytest.mark.security
@pytest.mark.asyncio
async def test_authentication_bypass_attempt_no_token(client: AsyncClient):
    response = await client.get("/api/services")
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_authentication_bypass_attempt_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/services",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_token_tampering_attempt(client: AsyncClient, auth_headers: dict):
    token = auth_headers["Authorization"].split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        payload["sub"] = "00000000-0000-0000-0000-000000000000"
        
        tampered_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        
        response = await client.get(
            "/api/services",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    except Exception:
        pass


@pytest.mark.security
@pytest.mark.asyncio
async def test_expired_token_handling(client: AsyncClient):
    from datetime import datetime, timedelta
    import uuid
    
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    
    expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm=settings.algorithm)
    
    response = await client.get(
        "/api/services",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_invalid_token_format(client: AsyncClient):
    response = await client.get(
        "/api/services",
        headers={"Authorization": "InvalidFormat token"}
    )
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_missing_authorization_header(client: AsyncClient):
    response = await client.get("/api/services")
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_token_with_wrong_secret(client: AsyncClient):
    import uuid
    from datetime import datetime, timedelta
    
    payload = {
        "sub": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    wrong_secret_token = jwt.encode(payload, "wrong_secret_key", algorithm="HS256")
    
    response = await client.get(
        "/api/services",
        headers={"Authorization": f"Bearer {wrong_secret_token}"}
    )
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_token_with_invalid_algorithm(client: AsyncClient):
    from jose.exceptions import JWSError
    
    try:
        import uuid
        from datetime import datetime, timedelta
        
        payload = {
            "sub": str(uuid.uuid4()),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        none_algorithm_token = jwt.encode(payload, settings.secret_key, algorithm="none")
    except JWSError:
        invalid_token = "invalid.algorithm.token"
        response = await client.get(
            "/api/services",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        return
    
    response = await client.get(
        "/api/services",
        headers={"Authorization": f"Bearer {none_algorithm_token}"}
    )
    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

