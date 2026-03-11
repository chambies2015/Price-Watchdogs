import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.service import Service, CheckFrequency
from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_subscription_free_tier(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    response = await client.get("/api/subscriptions/current", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan_type"] == "free"
    assert data["status"] == "active"
    assert data["service_limit"] == 3
    assert "current_service_count" in data


@pytest.mark.asyncio
async def test_get_current_subscription_pro_tier(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    subscription = Subscription(
        id=uuid4(),
        user_id=auth_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active,
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123"
    )
    db_session.add(subscription)
    await db_session.commit()
    
    response = await client.get("/api/subscriptions/current", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan_type"] == "pro_monthly"
    assert data["service_limit"] is None


@pytest.mark.asyncio
async def test_create_checkout_session_requires_auth(client: AsyncClient):
    response = await client.post(
        "/api/subscriptions/create-checkout",
        json={"plan_type": "pro_monthly"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_checkout_session_free_plan_error(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/subscriptions/create-checkout",
        json={"plan_type": "free"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "free" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancel_subscription_free_plan_error(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/subscriptions/cancel", headers=auth_headers)
    
    assert response.status_code == 400
    assert "free" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_payments_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/subscriptions/payments", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_service_limit_enforcement_free_tier(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    subscription = Subscription(
        id=uuid4(),
        user_id=auth_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    
    for i in range(3):
        service = Service(
            id=uuid4(),
            user_id=auth_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    response = await client.post(
        "/api/services",
        json={
            "name": "Fourth Service",
            "url": "https://example4.com",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert "limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_service_limit_enforcement_pro_tier_unlimited(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    subscription = Subscription(
        id=uuid4(),
        user_id=auth_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    for i in range(5):
        response = await client.post(
            "/api/services",
            json={
                "name": f"Service {i}",
                "url": f"https://example{i}.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_check_frequency_validation_free_tier(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    subscription = Subscription(
        id=uuid4(),
        user_id=auth_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "check_frequency": "twice_daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert "frequency" in response.json()["detail"].lower() or "pro" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_check_frequency_validation_pro_tier_allows_twice_daily(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    subscription = Subscription(
        id=uuid4(),
        user_id=auth_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    response = await client.post(
        "/api/services",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "check_frequency": "twice_daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201

