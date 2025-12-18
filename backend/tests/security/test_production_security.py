import pytest
from httpx import AsyncClient
from fastapi import status
from app.config import settings


@pytest.mark.security
@pytest.mark.asyncio
async def test_cors_configuration(client: AsyncClient):
    response = await client.options(
        "/api/services",
        headers={
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    if settings.environment == "production":
        assert "Access-Control-Allow-Origin" not in response.headers or \
               response.headers["Access-Control-Allow-Origin"] != "*", \
               "CORS should not allow all origins in production"
    else:
        pass


@pytest.mark.security
@pytest.mark.asyncio
async def test_rate_limiting_enforced(client: AsyncClient):
    responses = []
    for _ in range(15):
        response = await client.post("/api/auth/login", json={
            "email": "ratelimit@example.com",
            "password": "wrongpassword"
        })
        responses.append(response.status_code)
    
    rate_limited = any(r == status.HTTP_429_TOO_MANY_REQUESTS for r in responses)
    assert rate_limited, "Rate limiting should be enforced on auth endpoints"


@pytest.mark.security
@pytest.mark.asyncio
async def test_input_sanitization(client: AsyncClient, auth_headers: dict):
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "'; DROP TABLE services; --"
    ]
    
    for malicious_input in malicious_inputs:
        response = await client.post(
            "/api/services",
            json={
                "name": malicious_input,
                "url": "https://example.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert "<script>" not in data.get("name", ""), "Script tags should be sanitized"
            assert "javascript:" not in data.get("name", ""), "JavaScript protocol should be sanitized"


@pytest.mark.security
@pytest.mark.asyncio
async def test_https_enforced_in_production():
    if settings.environment == "production":
        assert settings.frontend_base_url.startswith("https://"), \
            "Frontend URL should use HTTPS in production"


@pytest.mark.security
@pytest.mark.asyncio
async def test_secret_key_not_exposed(client: AsyncClient):
    response = await client.get("/health")
    assert "secret_key" not in response.text.lower()
    assert "SECRET_KEY" not in response.text


@pytest.mark.security
@pytest.mark.asyncio
async def test_database_url_not_exposed(client: AsyncClient):
    response = await client.get("/health")
    assert "database" not in response.text.lower() or "postgres" not in response.text.lower()


@pytest.mark.security
@pytest.mark.asyncio
async def test_sensitive_headers_not_exposed(client: AsyncClient):
    response = await client.get("/health")
    headers = dict(response.headers)
    
    sensitive_headers = ["x-api-key", "authorization", "x-auth-token"]
    for header in sensitive_headers:
        assert header not in headers, f"Sensitive header {header} should not be exposed"


@pytest.mark.security
@pytest.mark.asyncio
async def test_error_messages_dont_expose_details(client: AsyncClient):
    response = await client.get(f"/api/services/{'invalid-uuid'}")
    
    if response.status_code >= 400:
        data = response.json()
        assert "traceback" not in str(data).lower()
        assert "stack trace" not in str(data).lower()
        assert "file" not in str(data).lower() or "line" not in str(data).lower()

