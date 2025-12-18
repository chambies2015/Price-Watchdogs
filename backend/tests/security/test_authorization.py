import pytest
from httpx import AsyncClient
from fastapi import status
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.service import Service, CheckFrequency
from app.core.security import get_password_hash


@pytest.mark.security
@pytest.mark.asyncio
async def test_unauthorized_service_access(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    other_user = User(
        id=uuid4(),
        email="other@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    
    other_service = Service(
        id=uuid4(),
        user_id=other_user.id,
        name="Other User Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(other_service)
    await db_session.commit()
    
    response = await client.get(
        f"/api/services/{other_service.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.security
@pytest.mark.asyncio
async def test_unauthorized_service_update(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    other_user = User(
        id=uuid4(),
        email="other2@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    
    other_service = Service(
        id=uuid4(),
        user_id=other_user.id,
        name="Other User Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(other_service)
    await db_session.commit()
    
    response = await client.put(
        f"/api/services/{other_service.id}",
        json={"name": "Hacked Service"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.security
@pytest.mark.asyncio
async def test_unauthorized_service_deletion(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    other_user = User(
        id=uuid4(),
        email="other3@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    
    other_service = Service(
        id=uuid4(),
        user_id=other_user.id,
        name="Other User Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(other_service)
    await db_session.commit()
    
    response = await client.delete(
        f"/api/services/{other_service.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.security
@pytest.mark.asyncio
async def test_subscription_based_access_control_free_tier(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
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
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    
    for i in range(3):
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
    
    response = await client.post(
        "/api/services",
        json={
            "name": "Fourth Service",
            "url": "https://example4.com",
            "check_frequency": "daily"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.security
@pytest.mark.asyncio
async def test_subscription_based_frequency_restriction(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
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
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.security
@pytest.mark.asyncio
async def test_list_services_only_returns_own_services(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    from app.models.user import User
    from sqlalchemy import select
    import uuid
    
    result = await db_session.execute(
        select(User).where(User.email == "authtest@example.com")
    )
    auth_user = result.scalar_one()
    
    other_user = User(
        id=uuid.uuid4(),
        email="other4@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    
    other_service = Service(
        id=uuid.uuid4(),
        user_id=other_user.id,
        name="Other User Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(other_service)
    
    my_service = Service(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        name="My Service",
        url="https://myexample.com",
        check_frequency=CheckFrequency.daily,
        is_active=True
    )
    db_session.add(my_service)
    await db_session.commit()
    
    response = await client.get("/api/services", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    service_ids = [s["id"] for s in data]
    assert str(my_service.id) in service_ids
    assert str(other_service.id) not in service_ids

