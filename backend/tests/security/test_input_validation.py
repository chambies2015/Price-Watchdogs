import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_in_service_name(client: AsyncClient, auth_headers: dict):
    malicious_inputs = [
        "'; DROP TABLE services; --",
        "' OR '1'='1",
        "'; DELETE FROM services WHERE '1'='1",
        "1' UNION SELECT * FROM users--"
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
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_403_FORBIDDEN]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data.get("name") == malicious_input


@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_in_url(client: AsyncClient, auth_headers: dict):
    malicious_inputs = [
        "https://example.com'; DROP TABLE services; --",
        "https://example.com' OR '1'='1",
    ]
    
    for malicious_input in malicious_inputs:
        response = await client.post(
            "/api/services",
            json={
                "name": "Test Service",
                "url": malicious_input,
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_xss_in_service_name(client: AsyncClient, auth_headers: dict):
    xss_payloads = [
        ("<script>alert('XSS')</script>", "alert('XSS')"),
        ("<img src=x onerror=alert('XSS')>", "x"),
        ("javascript:alert('XSS')", "alert('XSS')"),
        ("<svg onload=alert('XSS')>", "alert('XSS')")
    ]
    
    for payload, expected_sanitized in xss_payloads:
        response = await client.post(
            "/api/services",
            json={
                "name": payload,
                "url": "https://example.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "<script>" not in data.get("name", ""), "Script tags should be sanitized"
            assert "javascript:" not in data.get("name", ""), "JavaScript protocol should be sanitized"
            sanitized_name = data.get("name", "")
            assert sanitized_name == expected_sanitized or sanitized_name == "Untitled Service"


@pytest.mark.security
@pytest.mark.asyncio
async def test_path_traversal_attempt(client: AsyncClient, auth_headers: dict):
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/etc/passwd",
        "C:\\Windows\\System32"
    ]
    
    for path in malicious_paths:
        response = await client.post(
            "/api/services",
            json={
                "name": "Test",
                "url": f"https://example.com/{path}",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_command_injection_attempt(client: AsyncClient, auth_headers: dict):
    command_injections = [
        "; ls -la",
        "| cat /etc/passwd",
        "&& rm -rf /",
        "`whoami`"
    ]
    
    for injection in command_injections:
        response = await client.post(
            "/api/services",
            json={
                "name": f"Test{injection}",
                "url": "https://example.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_oversized_input_handling(client: AsyncClient, auth_headers: dict):
    oversized_name = "A" * 10000
    oversized_url = "https://example.com/" + "A" * 10000
    
    response = await client.post(
        "/api/services",
        json={
            "name": oversized_name,
            "url": oversized_url,
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.security
@pytest.mark.asyncio
async def test_special_characters_handling(client: AsyncClient, auth_headers: dict):
    special_chars = [
        "!@#$%^&*()",
        "测试服务",
        "🚀 Service",
        "Service\nWith\nNewlines"
    ]
    
    for special in special_chars:
        response = await client.post(
            "/api/services",
            json={
                "name": special,
                "url": "https://example.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_403_FORBIDDEN]


@pytest.mark.security
@pytest.mark.asyncio
async def test_null_byte_injection(client: AsyncClient, auth_headers: dict):
    null_byte_inputs = [
        "test\x00service",
        "https://example.com\x00/path"
    ]
    
    for null_input in null_byte_inputs:
        response = await client.post(
            "/api/services",
            json={
                "name": null_input,
                "url": "https://example.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_403_FORBIDDEN]

