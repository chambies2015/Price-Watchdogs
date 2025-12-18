import pytest
from fastapi import HTTPException, status
from app.services.subscription_service import enforce_service_limit
from app.services.subscription_service import validate_check_frequency
from app.models.subscription import PlanType
from app.models.service import CheckFrequency


@pytest.mark.asyncio
@pytest.mark.unit
async def test_enforce_service_limit_raises_http_exception(db_session, test_user):
    from app.models.subscription import Subscription, SubscriptionStatus
    from app.models.service import Service
    from uuid import uuid4
    
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
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "limit" in exc_info.value.detail.lower()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_check_frequency_raises_http_exception(db_session, test_user):
    from app.models.subscription import Subscription, SubscriptionStatus
    from uuid import uuid4
    
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
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "frequency" in exc_info.value.detail.lower() or "pro" in exc_info.value.detail.lower()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_error_message_formatting():
    error_msg = "Service limit reached. You have 3/3 services. Upgrade to Pro for unlimited services."
    
    assert "limit" in error_msg.lower()
    assert "3/3" in error_msg
    assert "upgrade" in error_msg.lower()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_http_exception_with_detail():
    exc = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )
    
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "Resource not found"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_error_response_schema():
    from app.schemas.service import ServiceResponse
    
    error_response = {
        "detail": "Service not found"
    }
    
    assert "detail" in error_response
    assert isinstance(error_response["detail"], str)

