import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import uuid
from app.services.email_service import render_alert_email, send_alert_email
from app.models.change_event import ChangeEvent, ChangeType
from app.models.service import Service, CheckFrequency
from app.models.user import User
from app.models.snapshot import Snapshot
from app.services.processor import generate_hash


@pytest.fixture
def mock_change_event():
    return ChangeEvent(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        old_snapshot_id=uuid.uuid4(),
        new_snapshot_id=uuid.uuid4(),
        change_type=ChangeType.price_increase,
        summary="Price increase detected: average price increased by $5.00",
        confidence_score=0.85,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_service():
    return Service(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Service",
        url="https://example.com/pricing",
        check_frequency=CheckFrequency.daily
    )


@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed"
    )


@pytest.fixture
def mock_old_snapshot():
    return Snapshot(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        raw_html_hash=generate_hash("old content"),
        normalized_content_hash=generate_hash("old content"),
        normalized_content="Basic Plan: $10 per month\nPro Plan: $20 per month"
    )


@pytest.fixture
def mock_new_snapshot():
    return Snapshot(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        raw_html_hash=generate_hash("new content"),
        normalized_content_hash=generate_hash("new content"),
        normalized_content="Basic Plan: $15 per month\nPro Plan: $25 per month"
    )


def test_render_alert_email(mock_change_event, mock_service, mock_user, mock_old_snapshot, mock_new_snapshot):
    html, text = render_alert_email(
        mock_change_event,
        mock_service,
        mock_user,
        mock_old_snapshot,
        mock_new_snapshot
    )
    
    assert isinstance(html, str)
    assert isinstance(text, str)
    assert mock_service.name in html
    assert mock_service.name in text
    assert mock_service.url in html
    assert mock_service.url in text
    assert "Price Increase" in html
    assert mock_change_event.summary in html
    assert mock_change_event.summary in text
    assert "85%" in html
    assert mock_old_snapshot.normalized_content[:20] in html
    assert mock_new_snapshot.normalized_content[:20] in html


def test_render_alert_email_no_old_snapshot(mock_change_event, mock_service, mock_user, mock_new_snapshot):
    html, text = render_alert_email(
        mock_change_event,
        mock_service,
        mock_user,
        None,
        mock_new_snapshot
    )
    
    assert isinstance(html, str)
    assert isinstance(text, str)
    assert mock_service.name in html
    assert "After:" in html


@pytest.mark.asyncio
@patch('app.services.email_service.settings')
@patch('app.services.email_service.httpx.AsyncClient')
async def test_send_alert_email_success(
    mock_client_class,
    mock_settings,
    mock_change_event,
    mock_service,
    mock_user,
    mock_old_snapshot,
    mock_new_snapshot
):
    mock_settings.mailgun_api_key = "test-api-key"
    mock_settings.mailgun_domain = "test-domain.com"
    mock_settings.mailgun_from_email = "noreply@test.com"
    mock_settings.mailgun_api_base_url = "https://api.mailgun.net"
    mock_settings.frontend_base_url = "http://localhost:3000"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await send_alert_email(
        mock_change_event,
        mock_service,
        mock_user,
        mock_old_snapshot,
        mock_new_snapshot
    )
    
    assert result is True
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
@patch('app.services.email_service.settings')
async def test_send_alert_email_missing_config(
    mock_settings,
    mock_change_event,
    mock_service,
    mock_user,
    mock_old_snapshot,
    mock_new_snapshot
):
    mock_settings.mailgun_api_key = None
    mock_settings.mailgun_domain = None
    mock_settings.mailgun_from_email = None
    
    result = await send_alert_email(
        mock_change_event,
        mock_service,
        mock_user,
        mock_old_snapshot,
        mock_new_snapshot
    )
    
    assert result is False


@pytest.mark.asyncio
@patch('app.services.email_service.settings')
@patch('app.services.email_service.httpx.AsyncClient')
async def test_send_alert_email_api_error(
    mock_client_class,
    mock_settings,
    mock_change_event,
    mock_service,
    mock_user,
    mock_old_snapshot,
    mock_new_snapshot
):
    mock_settings.mailgun_api_key = "test-api-key"
    mock_settings.mailgun_domain = "test-domain.com"
    mock_settings.mailgun_from_email = "noreply@test.com"
    mock_settings.mailgun_api_base_url = "https://api.mailgun.net"
    mock_settings.frontend_base_url = "http://localhost:3000"
    
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await send_alert_email(
        mock_change_event,
        mock_service,
        mock_user,
        mock_old_snapshot,
        mock_new_snapshot
    )
    
    assert result is False


@pytest.mark.asyncio
@patch('app.services.email_service.settings')
@patch('app.services.email_service.httpx.AsyncClient')
async def test_send_alert_email_timeout(
    mock_client_class,
    mock_settings,
    mock_change_event,
    mock_service,
    mock_user,
    mock_old_snapshot,
    mock_new_snapshot
):
    import httpx
    
    mock_settings.mailgun_api_key = "test-api-key"
    mock_settings.mailgun_domain = "test-domain.com"
    mock_settings.mailgun_from_email = "noreply@test.com"
    mock_settings.mailgun_api_base_url = "https://api.mailgun.net"
    mock_settings.frontend_base_url = "http://localhost:3000"
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
    mock_client_class.return_value = mock_client
    
    result = await send_alert_email(
        mock_change_event,
        mock_service,
        mock_user,
        mock_old_snapshot,
        mock_new_snapshot
    )
    
    assert result is False

