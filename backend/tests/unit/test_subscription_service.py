import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.service import Service, CheckFrequency
from app.models.user import User
from app.services.subscription_service import (
    get_user_subscription,
    check_service_limit,
    enforce_service_limit,
    get_allowed_check_frequencies,
    can_use_check_frequency,
    validate_check_frequency
)
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_get_user_subscription_creates_free_tier(db_session: AsyncSession, test_user):
    subscription = await get_user_subscription(db_session, test_user.id)
    
    assert subscription is not None
    assert subscription.user_id == test_user.id
    assert subscription.plan_type == PlanType.free
    assert subscription.status == SubscriptionStatus.active


@pytest.mark.asyncio
async def test_get_user_subscription_returns_existing(db_session: AsyncSession, test_user):
    existing = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active
    )
    db_session.add(existing)
    await db_session.commit()
    
    subscription = await get_user_subscription(db_session, test_user.id)
    
    assert subscription.id == existing.id
    assert subscription.plan_type == PlanType.pro_monthly


@pytest.mark.asyncio
async def test_check_service_limit_free_tier(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    
    for i in range(2):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    can_create, current_count, limit = await check_service_limit(db_session, test_user.id)
    
    assert can_create is True
    assert current_count == 2
    assert limit == 3


@pytest.mark.asyncio
async def test_check_service_limit_free_tier_at_limit(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    
    for i in range(3):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    can_create, current_count, limit = await check_service_limit(db_session, test_user.id)
    
    assert can_create is False
    assert current_count == 3
    assert limit == 3


@pytest.mark.asyncio
async def test_check_service_limit_pro_tier(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    can_create, current_count, limit = await check_service_limit(db_session, test_user.id)
    
    assert can_create is True
    assert limit is None


@pytest.mark.asyncio
async def test_enforce_service_limit_allows_creation(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    await enforce_service_limit(db_session, test_user.id)


@pytest.mark.asyncio
async def test_enforce_service_limit_raises_at_limit(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    
    for i in range(3):
        service = Service(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Service {i}",
            url=f"https://example{i}.com",
            check_frequency=CheckFrequency.daily,
            is_active=True
        )
        db_session.add(service)
    
    await db_session.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        await enforce_service_limit(db_session, test_user.id)
    
    assert exc_info.value.status_code == 403
    assert "limit" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_allowed_check_frequencies_free_tier():
    frequencies = get_allowed_check_frequencies(PlanType.free)
    
    assert CheckFrequency.daily in frequencies
    assert CheckFrequency.weekly in frequencies
    assert CheckFrequency.twice_daily not in frequencies


@pytest.mark.asyncio
async def test_get_allowed_check_frequencies_pro_tier():
    frequencies = get_allowed_check_frequencies(PlanType.pro_monthly)
    
    assert CheckFrequency.daily in frequencies
    assert CheckFrequency.weekly in frequencies
    assert CheckFrequency.twice_daily in frequencies


@pytest.mark.asyncio
async def test_can_use_check_frequency_free_tier():
    assert can_use_check_frequency(PlanType.free, CheckFrequency.daily) is True
    assert can_use_check_frequency(PlanType.free, CheckFrequency.weekly) is True
    assert can_use_check_frequency(PlanType.free, CheckFrequency.twice_daily) is False


@pytest.mark.asyncio
async def test_can_use_check_frequency_pro_tier():
    assert can_use_check_frequency(PlanType.pro_monthly, CheckFrequency.daily) is True
    assert can_use_check_frequency(PlanType.pro_monthly, CheckFrequency.weekly) is True
    assert can_use_check_frequency(PlanType.pro_monthly, CheckFrequency.twice_daily) is True


@pytest.mark.asyncio
async def test_validate_check_frequency_allows_valid(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    await validate_check_frequency(db_session, test_user.id, CheckFrequency.daily)


@pytest.mark.asyncio
async def test_validate_check_frequency_raises_for_invalid(db_session: AsyncSession, test_user):
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_check_frequency(db_session, test_user.id, CheckFrequency.twice_daily)
    
    assert exc_info.value.status_code == 403
    assert "frequency" in exc_info.value.detail.lower() or "pro" in exc_info.value.detail.lower()

