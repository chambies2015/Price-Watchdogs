import pytest
from app.services.csv_service import (
    parse_services_csv,
    validate_service_row,
    generate_services_csv,
    generate_change_events_csv,
    generate_snapshots_csv,
)
from app.models.service import Service, CheckFrequency
from app.models.change_event import ChangeEvent, ChangeType
from app.models.snapshot import Snapshot
from datetime import datetime
import uuid


def test_parse_services_csv():
    csv_content = """name,url,check_frequency,is_active
Service 1,https://example.com/pricing,daily,true
Service 2,https://test.com/pricing,weekly,false"""
    
    rows = parse_services_csv(csv_content)
    
    assert len(rows) == 2
    assert rows[0]["name"] == "Service 1"
    assert rows[0]["url"] == "https://example.com/pricing"
    assert rows[1]["name"] == "Service 2"


def test_parse_services_csv_with_whitespace():
    csv_content = """name,url,check_frequency
  Service 1  ,  https://example.com/pricing  ,  daily  """
    
    rows = parse_services_csv(csv_content)
    
    assert len(rows) == 1
    assert rows[0]["name"] == "Service 1"
    assert rows[0]["url"] == "https://example.com/pricing"


def test_validate_service_row_valid():
    row = {
        "name": "Test Service",
        "url": "https://example.com/pricing",
        "check_frequency": "daily",
        "is_active": "true"
    }
    
    is_valid, error = validate_service_row(row, 1)
    
    assert is_valid is True
    assert error is None


def test_validate_service_row_missing_name():
    row = {
        "name": "",
        "url": "https://example.com/pricing"
    }
    
    is_valid, error = validate_service_row(row, 2)
    
    assert is_valid is False
    assert "name" in error.lower()


def test_validate_service_row_missing_url():
    row = {
        "name": "Test Service",
        "url": ""
    }
    
    is_valid, error = validate_service_row(row, 3)
    
    assert is_valid is False
    assert "url" in error.lower()


def test_validate_service_row_invalid_url():
    row = {
        "name": "Test Service",
        "url": "javascript:alert('xss')"
    }
    
    is_valid, error = validate_service_row(row, 4)
    
    assert is_valid is False
    assert "url" in error.lower()


def test_validate_service_row_invalid_frequency():
    row = {
        "name": "Test Service",
        "url": "https://example.com/pricing",
        "check_frequency": "invalid"
    }
    
    is_valid, error = validate_service_row(row, 5)
    
    assert is_valid is False
    assert "frequency" in error.lower()


def test_validate_service_row_url_without_scheme():
    row = {
        "name": "Test Service",
        "url": "example.com/pricing"
    }
    
    is_valid, error = validate_service_row(row, 6)
    
    assert is_valid is True


def test_generate_services_csv():
    services = [
        Service(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Service 1",
            url="https://example.com/pricing",
            check_frequency=CheckFrequency.daily,
            is_active=True,
            alerts_enabled=True,
            alert_confidence_threshold=0.6,
            created_at=datetime.utcnow(),
            last_checked_at=datetime.utcnow()
        ),
        Service(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Service 2",
            url="https://test.com/pricing",
            check_frequency=CheckFrequency.weekly,
            is_active=False,
            alerts_enabled=False,
            alert_confidence_threshold=0.7,
            created_at=datetime.utcnow(),
            last_checked_at=None
        )
    ]
    
    csv_content = generate_services_csv(services)
    
    assert "id,name,url,check_frequency" in csv_content
    assert "Service 1" in csv_content
    assert "Service 2" in csv_content
    assert "daily" in csv_content
    assert "weekly" in csv_content
    assert "true" in csv_content
    assert "false" in csv_content


def test_generate_change_events_csv():
    service_id = uuid.uuid4()
    service_names = {service_id: "Test Service"}
    
    events = [
        ChangeEvent(
            id=uuid.uuid4(),
            service_id=service_id,
            old_snapshot_id=None,
            new_snapshot_id=uuid.uuid4(),
            change_type=ChangeType.price_increase,
            summary="Price increased",
            confidence_score=0.85,
            created_at=datetime.utcnow()
        )
    ]
    
    csv_content = generate_change_events_csv(events, service_names)
    
    assert "id,service_id,service_name,change_type" in csv_content
    assert "Test Service" in csv_content
    assert "price_increase" in csv_content
    assert "Price increased" in csv_content


def test_generate_snapshots_csv():
    service_id = uuid.uuid4()
    service_names = {service_id: "Test Service"}
    
    snapshots = [
        Snapshot(
            id=uuid.uuid4(),
            service_id=service_id,
            raw_html_hash="hash1",
            normalized_content_hash="hash2",
            normalized_content="content",
            created_at=datetime.utcnow()
        )
    ]
    
    csv_content = generate_snapshots_csv(snapshots, service_names)
    
    assert "id,service_id,service_name,created_at" in csv_content
    assert "Test Service" in csv_content
    assert "hash2" in csv_content
