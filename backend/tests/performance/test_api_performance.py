import pytest
import time
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.performance
@pytest.mark.asyncio
async def test_list_services_performance(client: AsyncClient, auth_headers: dict, db_session):
    from app.models.user import User
    from app.models.service import Service, CheckFrequency
    from sqlalchemy import select
    import uuid
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    for i in range(10):
        service = Service(
            id=uuid.uuid4(),
            user_id=auth_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    start_time = time.time()
    response = await client.get("/api/services", headers=auth_headers)
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed < 0.2


@pytest.mark.performance
@pytest.mark.asyncio
async def test_get_service_performance(client: AsyncClient, auth_headers: dict, db_session):
    from app.models.user import User
    from app.models.service import Service, CheckFrequency
    from sqlalchemy import select
    import uuid
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    service = Service(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(service)
    await db_session.commit()
    
    start_time = time.time()
    response = await client.get(f"/api/services/{service.id}", headers=auth_headers)
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed < 0.2


@pytest.mark.performance
@pytest.mark.asyncio
async def test_create_service_performance(client: AsyncClient, auth_headers: dict):
    start_time = time.time()
    response = await client.post(
        "/api/services",
        json={
            "name": "Performance Test Service",
            "url": "https://example.com",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    elapsed = time.time() - start_time
    
    assert response.status_code == 201
    assert elapsed < 0.3


@pytest.mark.performance
@pytest.mark.asyncio
async def test_dashboard_summary_performance(client: AsyncClient, auth_headers: dict, db_session):
    from app.models.user import User
    from app.models.service import Service, CheckFrequency
    from app.models.change_event import ChangeEvent, ChangeType
    from sqlalchemy import select
    import uuid
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    for i in range(5):
        service = Service(
            id=uuid.uuid4(),
            user_id=auth_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
        await db_session.flush()
        
        change_event = ChangeEvent(
            id=uuid.uuid4(),
            service_id=service.id,
            new_snapshot_id=uuid.uuid4(),
            change_type=ChangeType.price_increase,
            summary=f"Change {i}",
            confidence_score=0.8
        )
        db_session.add(change_event)
    
    await db_session.commit()
    
    start_time = time.time()
    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed < 0.5


@pytest.mark.performance
@pytest.mark.asyncio
async def test_get_subscription_performance(client: AsyncClient, auth_headers: dict):
    start_time = time.time()
    response = await client.get("/api/subscriptions/current", headers=auth_headers)
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed < 0.2


@pytest.mark.performance
@pytest.mark.asyncio
async def test_batch_service_creation_performance(client: AsyncClient, auth_headers: dict, db_session):
    from app.models.user import User
    from app.models.subscription import Subscription, PlanType, SubscriptionStatus
    from sqlalchemy import select
    import uuid
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    start_time = time.time()
    
    for i in range(5):
        response = await client.post(
            "/api/services",
            json={
                "name": f"Batch Service {i}",
                "url": f"https://example{i}.com",
                "check_frequency": "daily"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
    
    elapsed = time.time() - start_time
    
    assert elapsed < 2.0

