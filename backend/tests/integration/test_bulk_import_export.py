import pytest
from httpx import AsyncClient
import io


@pytest.mark.asyncio
async def test_export_services_csv(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/services",
        json={
            "name": "Service 1",
            "url": "https://example.com/pricing1",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    await client.post(
        "/api/services",
        json={
            "name": "Service 2",
            "url": "https://example.com/pricing2",
            "check_frequency": "weekly"
        },
        headers=auth_headers
    )
    
    response = await client.get("/api/services/export", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert "attachment" in response.headers["Content-Disposition"]
    
    content = response.text
    assert "id,name,url,check_frequency" in content
    assert "Service 1" in content
    assert "Service 2" in content


@pytest.mark.asyncio
async def test_import_services_csv_valid(client: AsyncClient, auth_headers: dict):
    csv_content = """name,url,check_frequency,is_active
Imported Service 1,https://example.com/pricing1,daily,true
Imported Service 2,https://example.com/pricing2,weekly,false"""
    
    files = {
        "file": ("services.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = await client.post(
        "/api/services/import",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["created"] == 2
    assert data["failed"] == 0
    assert len(data["services"]) == 2
    
    list_response = await client.get("/api/services", headers=auth_headers)
    services = list_response.json()
    service_names = [s["name"] for s in services]
    assert "Imported Service 1" in service_names
    assert "Imported Service 2" in service_names


@pytest.mark.asyncio
async def test_import_services_csv_with_errors(client: AsyncClient, auth_headers: dict):
    csv_content = """name,url,check_frequency,is_active
Valid Service,https://example.com/pricing,daily,true
Invalid Service,,daily,true
Another Invalid,not-a-url,daily,true"""
    
    files = {
        "file": ("services.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = await client.post(
        "/api/services/import",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["created"] == 1
    assert data["failed"] == 2
    assert len(data["errors"]) == 2
    assert any("url" in err.lower() for err in data["errors"])


@pytest.mark.asyncio
async def test_import_services_csv_invalid_file_type(client: AsyncClient, auth_headers: dict):
    files = {
        "file": ("services.txt", io.BytesIO(b"not a csv"), "text/plain")
    }
    
    response = await client.post(
        "/api/services/import",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_services_csv_empty_file(client: AsyncClient, auth_headers: dict):
    csv_content = """name,url"""
    
    files = {
        "file": ("services.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = await client.post(
        "/api/services/import",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_services_csv_url_normalization(client: AsyncClient, auth_headers: dict):
    csv_content = """name,url
Service Without Scheme,example.com/pricing"""
    
    files = {
        "file": ("services.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = await client.post(
        "/api/services/import",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["created"] == 1
    service = data["services"][0]
    assert service["url"].startswith("https://")


@pytest.mark.asyncio
async def test_import_services_csv_enforces_service_limit(client: AsyncClient, auth_headers: dict, db_session):
    from app.models.user import User
    from app.models.subscription import Subscription, PlanType, SubscriptionStatus
    from app.models.service import Service, CheckFrequency
    from sqlalchemy import select
    import uuid
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    user = result.scalar_one_or_none()
    
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    
    existing_service_1 = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Existing Service 1",
        url="https://example.com/existing1",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    existing_service_2 = Service(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Existing Service 2",
        url="https://example.com/existing2",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(existing_service_1)
    db_session.add(existing_service_2)
    await db_session.commit()
    
    csv_content = """name,url
Service 1,https://example.com/pricing1
Service 2,https://example.com/pricing2"""
    
    files = {
        "file": ("services.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    
    response = await client.post(
        "/api/services/import",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["created"] == 1
    assert data["failed"] >= 1
