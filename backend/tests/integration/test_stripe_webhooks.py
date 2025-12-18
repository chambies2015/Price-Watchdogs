import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.payment import Payment
from app.models.user import User
from unittest.mock import patch
import json
import hmac
import hashlib
import time


def create_stripe_signature(payload: bytes, secret: str) -> str:
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload.decode()}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.mark.asyncio
async def test_webhook_checkout_session_completed(client: AsyncClient, db_session: AsyncSession, test_user):
    from app.config import settings
    
    if not settings.stripe_webhook_secret:
        pytest.skip("Stripe webhook secret not configured")
    
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.free,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    await db_session.commit()
    
    event_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test123",
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {
                    "user_id": str(test_user.id),
                    "plan_type": "pro_monthly"
                }
            }
        }
    }
    
    payload = json.dumps(event_payload).encode()
    signature = create_stripe_signature(payload, settings.stripe_webhook_secret)
    
    with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event_payload
        
        response = await client.post(
            "/api/subscriptions/webhook",
            content=payload,
            headers={"stripe-signature": signature}
        )
        
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Subscription).where(Subscription.user_id == test_user.id)
        )
        updated_subscription = result.scalar_one()
        
        assert updated_subscription.stripe_customer_id == "cus_test123"
        assert updated_subscription.stripe_subscription_id == "sub_test123"
        assert updated_subscription.plan_type == PlanType.pro_monthly


@pytest.mark.asyncio
async def test_webhook_subscription_updated(client: AsyncClient, db_session: AsyncSession, test_user):
    from app.config import settings
    
    if not settings.stripe_webhook_secret:
        pytest.skip("Stripe webhook secret not configured")
    
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active,
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123"
    )
    db_session.add(subscription)
    await db_session.commit()
    
    event_payload = {
        "id": "evt_test456",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "status": "active",
                "cancel_at_period_end": True,
                "current_period_start": int(time.time()),
                "current_period_end": int(time.time()) + 2592000
            }
        }
    }
    
    payload = json.dumps(event_payload).encode()
    signature = create_stripe_signature(payload, settings.stripe_webhook_secret)
    
    with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event_payload
        
        response = await client.post(
            "/api/subscriptions/webhook",
            content=payload,
            headers={"stripe-signature": signature}
        )
        
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Subscription).where(Subscription.id == subscription.id)
        )
        updated_subscription = result.scalar_one()
        
        assert updated_subscription.cancel_at_period_end is True


@pytest.mark.asyncio
async def test_webhook_subscription_deleted(client: AsyncClient, db_session: AsyncSession, test_user):
    from app.config import settings
    
    if not settings.stripe_webhook_secret:
        pytest.skip("Stripe webhook secret not configured")
    
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active,
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123"
    )
    db_session.add(subscription)
    await db_session.commit()
    
    event_payload = {
        "id": "evt_test789",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test123"
            }
        }
    }
    
    payload = json.dumps(event_payload).encode()
    signature = create_stripe_signature(payload, settings.stripe_webhook_secret)
    
    with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event_payload
        
        response = await client.post(
            "/api/subscriptions/webhook",
            content=payload,
            headers={"stripe-signature": signature}
        )
        
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Subscription).where(Subscription.id == subscription.id)
        )
        updated_subscription = result.scalar_one()
        
        assert updated_subscription.status == SubscriptionStatus.canceled
        assert updated_subscription.plan_type == PlanType.free
        assert updated_subscription.stripe_subscription_id is None


@pytest.mark.asyncio
async def test_webhook_payment_succeeded(client: AsyncClient, db_session: AsyncSession, test_user):
    from app.config import settings
    
    if not settings.stripe_webhook_secret:
        pytest.skip("Stripe webhook secret not configured")
    
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active,
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123"
    )
    db_session.add(subscription)
    await db_session.commit()
    
    event_payload = {
        "id": "evt_payment123",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": "in_test123",
                "subscription": "sub_test123",
                "amount_paid": 900,
                "currency": "usd"
            }
        }
    }
    
    payload = json.dumps(event_payload).encode()
    signature = create_stripe_signature(payload, settings.stripe_webhook_secret)
    
    with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event_payload
        
        response = await client.post(
            "/api/subscriptions/webhook",
            content=payload,
            headers={"stripe-signature": signature}
        )
        
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Payment).where(Payment.user_id == test_user.id)
        )
        payments = result.scalars().all()
        
        assert len(payments) > 0
        payment = payments[0]
        assert payment.amount == 900
        assert payment.currency == "usd"
        assert payment.status == "succeeded"


@pytest.mark.asyncio
async def test_webhook_payment_failed(client: AsyncClient, db_session: AsyncSession, test_user):
    from app.config import settings
    
    if not settings.stripe_webhook_secret:
        pytest.skip("Stripe webhook secret not configured")
    
    subscription = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_type=PlanType.pro_monthly,
        status=SubscriptionStatus.active,
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123"
    )
    db_session.add(subscription)
    await db_session.commit()
    
    event_payload = {
        "id": "evt_payment456",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_test456",
                "subscription": "sub_test123",
                "amount_due": 900,
                "currency": "usd"
            }
        }
    }
    
    payload = json.dumps(event_payload).encode()
    signature = create_stripe_signature(payload, settings.stripe_webhook_secret)
    
    with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event_payload
        
        response = await client.post(
            "/api/subscriptions/webhook",
            content=payload,
            headers={"stripe-signature": signature}
        )
        
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(Subscription).where(Subscription.id == subscription.id)
        )
        updated_subscription = result.scalar_one()
        
        assert updated_subscription.status == SubscriptionStatus.past_due

