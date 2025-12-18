import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.stripe_service import (
    create_customer,
    create_subscription,
    cancel_subscription,
    update_subscription,
    get_subscription,
    create_checkout_session,
    handle_webhook_event
)


@pytest.mark.asyncio
async def test_create_customer_success():
    mock_customer = MagicMock()
    mock_customer.id = "cus_test123"
    
    with patch('app.services.stripe_service.stripe.Customer.create', return_value=mock_customer):
        customer = await create_customer("test@example.com", "user123")
        
        assert customer.id == "cus_test123"


@pytest.mark.asyncio
async def test_create_customer_error():
    import stripe
    
    with patch('app.services.stripe_service.stripe.Customer.create', side_effect=stripe.error.StripeError("API Error")):
        with pytest.raises(stripe.error.StripeError):
            await create_customer("test@example.com", "user123")


@pytest.mark.asyncio
async def test_create_subscription_success():
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    
    with patch('app.services.stripe_service.get_price_id_for_plan', return_value="price_test123"), \
         patch('app.services.stripe_service.stripe.Subscription.create', return_value=mock_subscription):
        subscription = await create_subscription("cus_test123", "pro_monthly")
        
        assert subscription.id == "sub_test123"


@pytest.mark.asyncio
async def test_create_subscription_invalid_plan():
    with patch('app.services.stripe_service.get_price_id_for_plan', return_value=None):
        with pytest.raises(ValueError, match="Invalid plan type"):
            await create_subscription("cus_test123", "invalid_plan")


@pytest.mark.asyncio
async def test_cancel_subscription_at_period_end():
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    
    with patch('app.services.stripe_service.stripe.Subscription.modify', return_value=mock_subscription):
        subscription = await cancel_subscription("sub_test123", cancel_at_period_end=True)
        
        assert subscription.id == "sub_test123"


@pytest.mark.asyncio
async def test_cancel_subscription_immediately():
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    
    with patch('app.services.stripe_service.stripe.Subscription.delete', return_value=mock_subscription):
        subscription = await cancel_subscription("sub_test123", cancel_at_period_end=False)
        
        assert subscription.id == "sub_test123"


@pytest.mark.asyncio
async def test_update_subscription_success():
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    mock_subscription["items"] = {"data": [MagicMock(id="item_test123")]}
    
    with patch('app.services.stripe_service.get_price_id_for_plan', return_value="price_test456"), \
         patch('app.services.stripe_service.stripe.Subscription.retrieve', return_value=mock_subscription), \
         patch('app.services.stripe_service.stripe.Subscription.modify', return_value=mock_subscription):
        subscription = await update_subscription("sub_test123", "pro_annual")
        
        assert subscription.id == "sub_test123"


@pytest.mark.asyncio
async def test_get_subscription_success():
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    
    with patch('app.services.stripe_service.stripe.Subscription.retrieve', return_value=mock_subscription):
        subscription = await get_subscription("sub_test123")
        
        assert subscription.id == "sub_test123"


@pytest.mark.asyncio
async def test_create_checkout_session_success():
    mock_session = MagicMock()
    mock_session.id = "cs_test123"
    mock_session.url = "https://checkout.stripe.com/test"
    
    with patch('app.services.stripe_service.get_price_id_for_plan', return_value="price_test123"), \
         patch('app.services.stripe_service.stripe.checkout.Session.create', return_value=mock_session):
        session = await create_checkout_session("cus_test123", "pro_monthly", "user123")
        
        assert session.id == "cs_test123"
        assert session.url == "https://checkout.stripe.com/test"


@pytest.mark.asyncio
async def test_handle_webhook_event_subscription_created():
    event = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "current_period_start": 1609459200,
                "current_period_end": 1612137600
            }
        }
    }
    
    result = await handle_webhook_event(event)
    
    assert result["processed"] is True
    assert result["event_type"] == "customer.subscription.created"
    assert result["data"]["subscription_id"] == "sub_test123"
    assert result["data"]["customer_id"] == "cus_test123"


@pytest.mark.asyncio
async def test_handle_webhook_event_subscription_updated():
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "status": "active",
                "cancel_at_period_end": False,
                "current_period_start": 1609459200,
                "current_period_end": 1612137600
            }
        }
    }
    
    result = await handle_webhook_event(event)
    
    assert result["processed"] is True
    assert result["event_type"] == "customer.subscription.updated"
    assert result["data"]["subscription_id"] == "sub_test123"


@pytest.mark.asyncio
async def test_handle_webhook_event_subscription_deleted():
    event = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test123"
            }
        }
    }
    
    result = await handle_webhook_event(event)
    
    assert result["processed"] is True
    assert result["event_type"] == "customer.subscription.deleted"
    assert result["data"]["subscription_id"] == "sub_test123"
    assert result["data"]["status"] == "canceled"


@pytest.mark.asyncio
async def test_handle_webhook_event_payment_succeeded():
    event = {
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
    
    result = await handle_webhook_event(event)
    
    assert result["processed"] is True
    assert result["event_type"] == "invoice.payment_succeeded"
    assert result["data"]["invoice_id"] == "in_test123"
    assert result["data"]["amount_paid"] == 900


@pytest.mark.asyncio
async def test_handle_webhook_event_payment_failed():
    event = {
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_test123",
                "subscription": "sub_test123",
                "amount_due": 900,
                "currency": "usd"
            }
        }
    }
    
    result = await handle_webhook_event(event)
    
    assert result["processed"] is True
    assert result["event_type"] == "invoice.payment_failed"
    assert result["data"]["invoice_id"] == "in_test123"


@pytest.mark.asyncio
async def test_handle_webhook_event_unknown():
    event = {
        "type": "unknown.event",
        "data": {
            "object": {}
        }
    }
    
    result = await handle_webhook_event(event)
    
    assert result["processed"] is False
    assert result["event_type"] == "unknown.event"

