from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
import uuid
import stripe
import logging
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.payment import Payment
from app.core.auth import get_current_user
from app.schemas.subscription import (
    SubscriptionResponse,
    PaymentResponse,
    CheckoutSessionResponse,
    CreateCheckoutRequest
)
from app.services.subscription_service import (
    get_user_subscription,
    check_service_limit,
    get_service_limit
)
from app.services.stripe_service import (
    create_customer,
    create_checkout_session,
    cancel_subscription,
    update_subscription,
    handle_webhook_event
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    subscription = await get_user_subscription(db, current_user.id)
    
    can_create, current_count, limit = await check_service_limit(db, current_user.id)
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan_type=subscription.plan_type,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        service_limit=limit,
        current_service_count=current_count,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at
    )


@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if request.plan_type == PlanType.free:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create checkout for free plan"
        )
    
    subscription = await get_user_subscription(db, current_user.id)
    
    customer_id = subscription.stripe_customer_id
    
    if not customer_id:
        customer = await create_customer(current_user.email, str(current_user.id))
        customer_id = customer.id
        subscription.stripe_customer_id = customer_id
        await db.commit()
    
    session = await create_checkout_session(
        customer_id,
        request.plan_type.value,
        str(current_user.id)
    )
    
    return CheckoutSessionResponse(
        session_id=session.id,
        url=session.url
    )


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    subscription = await get_user_subscription(db, current_user.id)
    
    if subscription.plan_type == PlanType.free:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Free plan cannot be canceled"
        )
    
    if not subscription.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel"
        )
    
    await cancel_subscription(subscription.stripe_subscription_id, cancel_at_period_end=True)
    
    subscription.cancel_at_period_end = True
    await db.commit()
    await db.refresh(subscription)
    
    can_create, current_count, limit = await check_service_limit(db, current_user.id)
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan_type=subscription.plan_type,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        service_limit=limit,
        current_service_count=current_count,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: Optional[str] = Header(None)
):
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured"
        )
    
    body = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            body,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    result = await handle_webhook_event(event)
    
    if not result["processed"]:
        return {"status": "ignored", "event_type": result["event_type"]}
    
    event_type = result["event_type"]
    data = result["data"]
    
    try:
        if event_type == "checkout.session.completed":
            session_data = event["data"]["object"]
            user_id_str = session_data.get("metadata", {}).get("user_id")
            plan_type_str = session_data.get("metadata", {}).get("plan_type")
            
            if user_id_str and plan_type_str:
                user_id = UUID(user_id_str)
                result_obj = await db.execute(
                    select(Subscription).where(Subscription.user_id == user_id)
                )
                subscription = result_obj.scalar_one_or_none()
                
                if subscription:
                    customer_id = session_data.get("customer")
                    subscription_id = session_data.get("subscription")
                    
                    if customer_id:
                        subscription.stripe_customer_id = customer_id
                    if subscription_id:
                        subscription.stripe_subscription_id = subscription_id
                        subscription.plan_type = PlanType(plan_type_str)
                        subscription.status = SubscriptionStatus.active
                        await db.commit()
        
        elif event_type == "customer.subscription.created":
            subscription_id = data.get("subscription_id")
            customer_id = data.get("customer_id")
            
            result_obj = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_customer_id == customer_id
                )
            )
            subscription = result_obj.scalar_one_or_none()
            
            if subscription:
                subscription.stripe_subscription_id = subscription_id
                subscription.status = SubscriptionStatus.active
                subscription.current_period_start = data.get("current_period_start")
                subscription.current_period_end = data.get("current_period_end")
                await db.commit()
        
        elif event_type == "customer.subscription.updated":
            subscription_id = data.get("subscription_id")
            
            result_obj = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == subscription_id
                )
            )
            subscription = result_obj.scalar_one_or_none()
            
            if subscription:
                status_str = data.get("status", "active")
                if status_str == "active":
                    subscription.status = SubscriptionStatus.active
                elif status_str == "past_due":
                    subscription.status = SubscriptionStatus.past_due
                elif status_str == "canceled":
                    subscription.status = SubscriptionStatus.canceled
                
                subscription.cancel_at_period_end = data.get("cancel_at_period_end", False)
                subscription.current_period_start = data.get("current_period_start")
                subscription.current_period_end = data.get("current_period_end")
                await db.commit()
        
        elif event_type == "customer.subscription.deleted":
            subscription_id = data.get("subscription_id")
            
            result_obj = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == subscription_id
                )
            )
            subscription = result_obj.scalar_one_or_none()
            
            if subscription:
                subscription.status = SubscriptionStatus.canceled
                subscription.plan_type = PlanType.free
                subscription.stripe_subscription_id = None
                await db.commit()
        
        elif event_type == "invoice.payment_succeeded":
            invoice_data = event["data"]["object"]
            subscription_id = invoice_data.get("subscription")
            
            if subscription_id:
                result_obj = await db.execute(
                    select(Subscription).where(
                        Subscription.stripe_subscription_id == subscription_id
                    )
                )
                subscription = result_obj.scalar_one_or_none()
                
                if subscription:
                    payment = Payment(
                        id=uuid.uuid4(),
                        user_id=subscription.user_id,
                        subscription_id=subscription.id,
                        stripe_invoice_id=invoice_data.get("id"),
                        amount=invoice_data.get("amount_paid", 0),
                        currency=invoice_data.get("currency", "usd"),
                        status="succeeded"
                    )
                    db.add(payment)
                    await db.commit()
        
        elif event_type == "invoice.payment_failed":
            invoice_data = event["data"]["object"]
            subscription_id = invoice_data.get("subscription")
            
            if subscription_id:
                result_obj = await db.execute(
                    select(Subscription).where(
                        Subscription.stripe_subscription_id == subscription_id
                    )
                )
                subscription = result_obj.scalar_one_or_none()
                
                if subscription:
                    subscription.status = SubscriptionStatus.past_due
                    await db.commit()
        
        return {"status": "success", "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.get("/payments", response_model=list[PaymentResponse])
async def get_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(50)
    )
    payments = result.scalars().all()
    
    return [PaymentResponse(
        id=payment.id,
        user_id=payment.user_id,
        subscription_id=payment.subscription_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        created_at=payment.created_at
    ) for payment in payments]

