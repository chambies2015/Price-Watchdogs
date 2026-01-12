from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID
import uuid
from datetime import datetime
import logging
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.service import Service, CheckFrequency
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_user_subscription(
    db: AsyncSession,
    user_id: UUID
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        subscription = Subscription(
            id=uuid.uuid4(),
            user_id=user_id,
            plan_type=PlanType.free,
            status=SubscriptionStatus.active
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        logger.info(f"Created free tier subscription for user {user_id}")
    
    return subscription


def get_service_limit(plan_type: PlanType) -> Optional[int]:
    if plan_type == PlanType.free:
        return 3
    elif plan_type in [PlanType.pro_monthly, PlanType.pro_annual]:
        return None
    return 3


async def check_service_limit(
    db: AsyncSession,
    user_id: UUID
) -> tuple[bool, int, Optional[int]]:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.is_admin:
        result = await db.execute(
            select(func.count(Service.id)).where(Service.user_id == user_id)
        )
        current_count = result.scalar() or 0
        return True, current_count, None
    
    subscription = await get_user_subscription(db, user_id)
    limit = get_service_limit(subscription.plan_type)
    
    result = await db.execute(
        select(func.count(Service.id)).where(Service.user_id == user_id)
    )
    current_count = result.scalar() or 0
    
    if limit is None:
        return True, current_count, None
    
    can_create = current_count < limit
    return can_create, current_count, limit


async def enforce_service_limit(
    db: AsyncSession,
    user_id: UUID
) -> None:
    can_create, current_count, limit = await check_service_limit(db, user_id)
    
    if not can_create:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Service limit reached. You have {current_count}/{limit} services. Upgrade to Pro for unlimited services."
        )


def get_allowed_check_frequencies(plan_type: PlanType) -> List[CheckFrequency]:
    if plan_type == PlanType.free:
        return [CheckFrequency.daily, CheckFrequency.weekly]
    elif plan_type in [PlanType.pro_monthly, PlanType.pro_annual]:
        return [CheckFrequency.daily, CheckFrequency.weekly, CheckFrequency.twice_daily]
    return [CheckFrequency.daily, CheckFrequency.weekly]


def can_use_check_frequency(plan_type: PlanType, frequency: CheckFrequency) -> bool:
    allowed = get_allowed_check_frequencies(plan_type)
    return frequency in allowed


async def validate_check_frequency(
    db: AsyncSession,
    user_id: UUID,
    frequency: CheckFrequency
) -> None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.is_admin:
        return
    
    subscription = await get_user_subscription(db, user_id)
    
    if not can_use_check_frequency(subscription.plan_type, frequency):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Check frequency '{frequency.value}' is only available for Pro plans. Upgrade to Pro to use faster checks."
        )

