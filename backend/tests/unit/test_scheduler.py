import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from app.models.service import Service, CheckFrequency
from app.scheduler import should_check_service


def test_should_check_service_no_last_checked():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=None
    )
    
    assert should_check_service(service) is True


def test_should_check_service_daily_due():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(hours=25)
    )
    
    assert should_check_service(service) is True


def test_should_check_service_daily_not_due():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(hours=12)
    )
    
    assert should_check_service(service) is False


def test_should_check_service_weekly_due():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.weekly,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(days=8)
    )
    
    assert should_check_service(service) is True


def test_should_check_service_weekly_not_due():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.weekly,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(days=3)
    )
    
    assert should_check_service(service) is False


def test_should_check_service_daily_exactly_24_hours():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.daily,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(hours=24)
    )
    
    assert should_check_service(service) is True


def test_should_check_service_weekly_exactly_7_days():
    service = Service(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Service",
        url="https://example.com",
        check_frequency=CheckFrequency.weekly,
        is_active=True,
        last_checked_at=datetime.utcnow() - timedelta(days=7)
    )
    
    assert should_check_service(service) is True

