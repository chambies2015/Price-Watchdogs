import pytest
from unittest.mock import patch, AsyncMock
from app.services.email_service import send_alert_email
from app.models.change_event import ChangeEvent, ChangeType
from app.models.service import Service
from app.models.user import User
from app.models.snapshot import Snapshot
from datetime import datetime
import uuid


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_email_service_connectivity():
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient', return_value=mock_client), \
         patch('app.services.email_service.settings') as mock_settings:
        mock_settings.mailgun_api_key = "test-key"
        mock_settings.mailgun_domain = "test-domain"
        mock_settings.mailgun_from_email = "test@example.com"
        
        change_event = ChangeEvent(
            id=uuid.uuid4(),
            service_id=uuid.uuid4(),
            change_type=ChangeType.price_increase,
            summary="Test change",
            confidence_score=0.8,
            created_at=datetime.utcnow()
        )
        
        service = Service(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Service",
            url="https://example.com"
        )
        
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        old_snapshot = Snapshot(
            id=uuid.uuid4(),
            service_id=service.id,
            normalized_content="Old content"
        )
        
        new_snapshot = Snapshot(
            id=uuid.uuid4(),
            service_id=service.id,
            normalized_content="New content"
        )
        
        result = await send_alert_email(
            change_event,
            service,
            user,
            old_snapshot,
            new_snapshot
        )
        
        assert result is True
        mock_client.post.assert_called_once()


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_email_service_handles_failure():
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient', return_value=mock_client), \
         patch('app.services.email_service.settings') as mock_settings:
        mock_settings.mailgun_api_key = "test-key"
        mock_settings.mailgun_domain = "test-domain"
        mock_settings.mailgun_from_email = "test@example.com"
        
        change_event = ChangeEvent(
            id=uuid.uuid4(),
            service_id=uuid.uuid4(),
            change_type=ChangeType.price_increase,
            summary="Test change",
            confidence_score=0.8,
            created_at=datetime.utcnow()
        )
        
        service = Service(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Service",
            url="https://example.com"
        )
        
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        old_snapshot = Snapshot(
            id=uuid.uuid4(),
            service_id=service.id,
            normalized_content="Old content"
        )
        
        new_snapshot = Snapshot(
            id=uuid.uuid4(),
            service_id=service.id,
            normalized_content="New content"
        )
        
        result = await send_alert_email(
            change_event,
            service,
            user,
            old_snapshot,
            new_snapshot
        )
        
        assert result is False

