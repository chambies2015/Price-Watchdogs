from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.subscription import PlanType, SubscriptionStatus


class SubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan_type: PlanType
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    service_limit: Optional[int] = None
    current_service_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_id: Optional[UUID] = None
    amount: int
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str


class CreateCheckoutRequest(BaseModel):
    plan_type: PlanType

