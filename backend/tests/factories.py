from faker import Faker
from uuid import uuid4
from datetime import datetime, timedelta
from app.models.user import User
from app.models.service import Service, CheckFrequency
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent, ChangeType
from app.models.alert import Alert
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.payment import Payment
from app.core.security import get_password_hash

fake = Faker()


def create_user(**kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "email": fake.email(),
        "password_hash": get_password_hash("testpassword123"),
        "created_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_service(user_id, **kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "name": fake.company() + " Pricing",
        "url": fake.url(),
        "check_frequency": CheckFrequency.daily,
        "is_active": True,
        "alerts_enabled": True,
        "alert_confidence_threshold": 0.6,
        "created_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_snapshot(service_id, **kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "service_id": service_id,
        "raw_html_hash": fake.sha256(),
        "normalized_content_hash": fake.sha256(),
        "normalized_content": fake.text(500),
        "created_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_change_event(service_id, old_snapshot_id=None, new_snapshot_id=None, **kwargs) -> dict:
    if not new_snapshot_id:
        new_snapshot_id = uuid4()
    
    defaults = {
        "id": uuid4(),
        "service_id": service_id,
        "old_snapshot_id": old_snapshot_id,
        "new_snapshot_id": new_snapshot_id,
        "change_type": ChangeType.price_increase,
        "summary": fake.sentence(),
        "confidence_score": 0.85,
        "created_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_alert(user_id, change_event_id, **kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "change_event_id": change_event_id,
        "sent_at": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_subscription(user_id, **kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "plan_type": PlanType.free,
        "status": SubscriptionStatus.active,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_payment(user_id, subscription_id=None, **kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "subscription_id": subscription_id,
        "amount": 900,
        "currency": "usd",
        "status": "succeeded",
        "created_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


async def create_test_user(db_session, **kwargs) -> User:
    user_data = create_user(**kwargs)
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def create_test_service(db_session, user_id, **kwargs) -> Service:
    service_data = create_service(user_id, **kwargs)
    service = Service(**service_data)
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


async def create_test_snapshot(db_session, service_id, **kwargs) -> Snapshot:
    snapshot_data = create_snapshot(service_id, **kwargs)
    snapshot = Snapshot(**snapshot_data)
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(snapshot)
    return snapshot


async def create_test_change_event(db_session, service_id, **kwargs) -> ChangeEvent:
    change_event_data = create_change_event(service_id, **kwargs)
    change_event = ChangeEvent(**change_event_data)
    db_session.add(change_event)
    await db_session.commit()
    await db_session.refresh(change_event)
    return change_event


async def create_test_subscription(db_session, user_id, **kwargs) -> Subscription:
    subscription_data = create_subscription(user_id, **kwargs)
    subscription = Subscription(**subscription_data)
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


async def create_test_payment(db_session, user_id, **kwargs) -> Payment:
    payment_data = create_payment(user_id, **kwargs)
    payment = Payment(**payment_data)
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment

