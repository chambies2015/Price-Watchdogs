import stripe
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


async def create_customer(email: str, user_id: str) -> Dict[str, Any]:
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": str(user_id)}
        )
        logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
        return customer
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe customer: {e}")
        raise


async def create_subscription(customer_id: str, plan_type: str) -> Dict[str, Any]:
    try:
        price_id = get_price_id_for_plan(plan_type)
        if not price_id:
            raise ValueError(f"Invalid plan type: {plan_type}")
        
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata={"plan_type": plan_type}
        )
        logger.info(f"Created Stripe subscription {subscription.id} for customer {customer_id}")
        return subscription
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe subscription: {e}")
        raise


async def cancel_subscription(subscription_id: str, cancel_at_period_end: bool = True) -> Dict[str, Any]:
    try:
        if cancel_at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.delete(subscription_id)
        
        logger.info(f"Canceled Stripe subscription {subscription_id}")
        return subscription
    except stripe.error.StripeError as e:
        logger.error(f"Error canceling Stripe subscription: {e}")
        raise


async def update_subscription(subscription_id: str, plan_type: str) -> Dict[str, Any]:
    try:
        price_id = get_price_id_for_plan(plan_type)
        if not price_id:
            raise ValueError(f"Invalid plan type: {plan_type}")
        
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": price_id
            }],
            metadata={"plan_type": plan_type},
            proration_behavior="always_invoice"
        )
        
        updated_subscription = stripe.Subscription.retrieve(subscription_id)
        logger.info(f"Updated Stripe subscription {subscription_id} to plan {plan_type}")
        return updated_subscription
    except stripe.error.StripeError as e:
        logger.error(f"Error updating Stripe subscription: {e}")
        raise


async def get_subscription(subscription_id: str) -> Dict[str, Any]:
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving Stripe subscription: {e}")
        raise


async def create_checkout_session(customer_id: Optional[str], plan_type: str, user_id: str) -> Dict[str, Any]:
    try:
        price_id = get_price_id_for_plan(plan_type)
        if not price_id:
            raise ValueError(f"Invalid plan type: {plan_type}")
        
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [{
                "price": price_id,
                "quantity": 1
            }],
            "mode": "subscription",
            "success_url": f"{settings.frontend_base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{settings.frontend_base_url}/checkout/cancel",
            "metadata": {
                "user_id": str(user_id),
                "plan_type": plan_type
            }
        }
        
        if customer_id:
            session_params["customer"] = customer_id
        
        session = stripe.checkout.Session.create(**session_params)
        logger.info(f"Created checkout session {session.id} for plan {plan_type}")
        return session
    except stripe.error.StripeError as e:
        logger.error(f"Error creating checkout session: {e}")
        raise


def get_price_id_for_plan(plan_type: str) -> Optional[str]:
    if not settings.stripe_secret_key:
        return None
    
    price_map = {
        "pro_monthly": getattr(settings, 'stripe_pro_monthly_price_id', None),
        "pro_annual": getattr(settings, 'stripe_pro_annual_price_id', None)
    }
    
    return price_map.get(plan_type)


async def handle_webhook_event(event: Dict[str, Any]) -> Dict[str, Any]:
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})
    
    result = {
        "processed": False,
        "event_type": event_type,
        "data": {}
    }
    
    try:
        if event_type == "customer.subscription.created":
            result["data"] = {
                "subscription_id": data.get("id"),
                "customer_id": data.get("customer"),
                "status": data.get("status"),
                "current_period_start": datetime.fromtimestamp(data.get("current_period_start", 0)),
                "current_period_end": datetime.fromtimestamp(data.get("current_period_end", 0))
            }
            result["processed"] = True
            
        elif event_type == "customer.subscription.updated":
            result["data"] = {
                "subscription_id": data.get("id"),
                "status": data.get("status"),
                "cancel_at_period_end": data.get("cancel_at_period_end", False),
                "current_period_start": datetime.fromtimestamp(data.get("current_period_start", 0)),
                "current_period_end": datetime.fromtimestamp(data.get("current_period_end", 0))
            }
            result["processed"] = True
            
        elif event_type == "customer.subscription.deleted":
            result["data"] = {
                "subscription_id": data.get("id"),
                "status": "canceled"
            }
            result["processed"] = True
            
        elif event_type == "invoice.payment_succeeded":
            result["data"] = {
                "invoice_id": data.get("id"),
                "subscription_id": data.get("subscription"),
                "amount_paid": data.get("amount_paid"),
                "currency": data.get("currency"),
                "status": "succeeded"
            }
            result["processed"] = True
            
        elif event_type == "invoice.payment_failed":
            result["data"] = {
                "invoice_id": data.get("id"),
                "subscription_id": data.get("subscription"),
                "amount_due": data.get("amount_due"),
                "currency": data.get("currency"),
                "status": "failed"
            }
            result["processed"] = True
        
        logger.info(f"Processed webhook event {event_type}: {result['processed']}")
        
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}")
        result["error"] = str(e)
    
    return result

