"""Unit tests for alert engine service."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from api.services.alert_engine import AlertEngine, AlertResult
from api.models.db.policy_change import PolicyChange
from api.models.db.route_subscription import RouteSubscription
from api.models.db.source import Source
from api.services.email_template import EmailContent


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_policy_change():
    """Sample PolicyChange instance."""
    change = Mock(spec=PolicyChange)
    change.id = uuid.uuid4()
    change.source_id = uuid.uuid4()
    change.diff = "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2"
    change.detected_at = datetime.utcnow()
    return change


@pytest.fixture
def sample_source():
    """Sample Source instance."""
    source = Mock(spec=Source)
    source.id = uuid.uuid4()
    source.country = "DE"
    source.visa_type = "Student"
    source.name = "Germany BMI"
    source.url = "https://example.com/germany-student-visa"
    return source


@pytest.fixture
def sample_route_subscription():
    """Sample RouteSubscription instance."""
    route = Mock(spec=RouteSubscription)
    route.id = uuid.uuid4()
    route.origin_country = "IN"
    route.destination_country = "DE"
    route.visa_type = "Student"
    route.email = "test@example.com"
    route.is_active = True
    return route


@pytest.fixture
def alert_engine(mock_db_session):
    """Create AlertEngine instance for testing."""
    with patch('api.services.alert_engine.get_email_service') as mock_get_email:
        mock_email_service = Mock()
        mock_get_email.return_value = mock_email_service
        
        engine = AlertEngine(mock_db_session)
        engine.email_service = mock_email_service
        return engine


@pytest.mark.asyncio
class TestAlertEngine:
    """Tests for AlertEngine service."""
    
    async def test_send_alerts_for_change_success(
        self, alert_engine, sample_policy_change, sample_source, sample_route_subscription
    ):
        """Test successful alert sending."""
        # Setup mocks
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=sample_policy_change)
        alert_engine.source_repo.get_by_id = AsyncMock(return_value=sample_source)
        alert_engine.route_mapper.get_routes_for_source = AsyncMock(return_value=[sample_route_subscription])
        
        # Mock email template service
        email_content = EmailContent(
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        alert_engine.email_template_service.render_change_alert_template = Mock(return_value=email_content)
        
        # Mock email service
        from api.integrations.resend import EmailResult
        email_result = EmailResult(success=True, message_id="email_123")
        alert_engine.email_service.send_email = Mock(return_value=email_result)
        
        # Mock email alert repository
        mock_alert = Mock()
        alert_engine.email_alert_repo.create = AsyncMock(return_value=mock_alert)
        
        # Execute
        result = await alert_engine.send_alerts_for_change(sample_policy_change.id)
        
        # Verify
        assert isinstance(result, AlertResult)
        assert result.policy_change_id == sample_policy_change.id
        assert result.routes_notified == 1
        assert result.emails_sent == 1
        assert result.emails_failed == 0
        assert len(result.errors) == 0
        
        # Verify email was sent
        alert_engine.email_service.send_email.assert_called_once()
        call_args = alert_engine.email_service.send_email.call_args
        assert call_args[1]['recipient'] == sample_route_subscription.email
        assert call_args[1]['subject'] == email_content.subject
        
        # Verify EmailAlert was created
        alert_engine.email_alert_repo.create.assert_called_once()
        alert_data = alert_engine.email_alert_repo.create.call_args[0][0]
        assert alert_data['policy_change_id'] == sample_policy_change.id
        assert alert_data['route_subscription_id'] == sample_route_subscription.id
        assert alert_data['status'] == "sent"
        assert alert_data['email_provider_id'] == "email_123"
    
    async def test_send_alerts_for_change_no_matching_routes(
        self, alert_engine, sample_policy_change, sample_source
    ):
        """Test alert sending when no routes match."""
        # Setup mocks
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=sample_policy_change)
        alert_engine.source_repo.get_by_id = AsyncMock(return_value=sample_source)
        alert_engine.route_mapper.get_routes_for_source = AsyncMock(return_value=[])
        
        # Execute
        result = await alert_engine.send_alerts_for_change(sample_policy_change.id)
        
        # Verify
        assert result.routes_notified == 0
        assert result.emails_sent == 0
        assert result.emails_failed == 0
        assert len(result.errors) == 0
        
        # Verify email was not sent
        alert_engine.email_service.send_email.assert_not_called()
    
    async def test_send_alerts_for_change_multiple_routes(
        self, alert_engine, sample_policy_change, sample_source
    ):
        """Test alert sending to multiple routes."""
        # Create multiple routes
        route1 = Mock(spec=RouteSubscription)
        route1.id = uuid.uuid4()
        route1.email = "user1@example.com"
        route1.is_active = True
        
        route2 = Mock(spec=RouteSubscription)
        route2.id = uuid.uuid4()
        route2.email = "user2@example.com"
        route2.is_active = True
        
        # Setup mocks
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=sample_policy_change)
        alert_engine.source_repo.get_by_id = AsyncMock(return_value=sample_source)
        alert_engine.route_mapper.get_routes_for_source = AsyncMock(return_value=[route1, route2])
        
        # Mock email template service
        email_content = EmailContent(
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        alert_engine.email_template_service.render_change_alert_template = Mock(return_value=email_content)
        
        # Mock email service - both succeed
        from api.integrations.resend import EmailResult
        email_result = EmailResult(success=True, message_id="email_123")
        alert_engine.email_service.send_email = Mock(return_value=email_result)
        
        # Mock email alert repository
        mock_alert = Mock()
        alert_engine.email_alert_repo.create = AsyncMock(return_value=mock_alert)
        
        # Execute
        result = await alert_engine.send_alerts_for_change(sample_policy_change.id)
        
        # Verify
        assert result.routes_notified == 2
        assert result.emails_sent == 2
        assert result.emails_failed == 0
        
        # Verify emails were sent to both routes
        assert alert_engine.email_service.send_email.call_count == 2
        assert alert_engine.email_alert_repo.create.call_count == 2
    
    async def test_send_alerts_for_change_email_failure_continues(
        self, alert_engine, sample_policy_change, sample_source, sample_route_subscription
    ):
        """Test that email failure for one route doesn't stop processing others."""
        # Create two routes
        route1 = Mock(spec=RouteSubscription)
        route1.id = uuid.uuid4()
        route1.email = "user1@example.com"
        route1.is_active = True
        
        route2 = Mock(spec=RouteSubscription)
        route2.id = uuid.uuid4()
        route2.email = "user2@example.com"
        route2.is_active = True
        
        # Setup mocks
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=sample_policy_change)
        alert_engine.source_repo.get_by_id = AsyncMock(return_value=sample_source)
        alert_engine.route_mapper.get_routes_for_source = AsyncMock(return_value=[route1, route2])
        
        # Mock email template service
        email_content = EmailContent(
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        alert_engine.email_template_service.render_change_alert_template = Mock(return_value=email_content)
        
        # Mock email service - first fails, second succeeds
        from api.integrations.resend import EmailResult
        email_results = [
            EmailResult(success=False, error="Email send failed"),
            EmailResult(success=True, message_id="email_123")
        ]
        alert_engine.email_service.send_email = Mock(side_effect=email_results)
        
        # Mock email alert repository
        mock_alert = Mock()
        alert_engine.email_alert_repo.create = AsyncMock(return_value=mock_alert)
        
        # Execute
        result = await alert_engine.send_alerts_for_change(sample_policy_change.id)
        
        # Verify
        assert result.routes_notified == 2
        assert result.emails_sent == 1
        assert result.emails_failed == 1
        assert len(result.errors) == 1
        assert "Failed to send alert" in result.errors[0]
        
        # Verify both emails were attempted
        assert alert_engine.email_service.send_email.call_count == 2
        assert alert_engine.email_alert_repo.create.call_count == 2
    
    async def test_send_alerts_for_change_exception_handling(
        self, alert_engine, sample_policy_change, sample_source, sample_route_subscription
    ):
        """Test that exceptions during email sending are handled gracefully."""
        # Setup mocks
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=sample_policy_change)
        alert_engine.source_repo.get_by_id = AsyncMock(return_value=sample_source)
        alert_engine.route_mapper.get_routes_for_source = AsyncMock(return_value=[sample_route_subscription])
        
        # Mock email template service to raise exception
        alert_engine.email_template_service.render_change_alert_template = Mock(
            side_effect=Exception("Template rendering failed")
        )
        
        # Mock email alert repository
        mock_alert = Mock()
        alert_engine.email_alert_repo.create = AsyncMock(return_value=mock_alert)
        
        # Execute
        result = await alert_engine.send_alerts_for_change(sample_policy_change.id)
        
        # Verify
        assert result.routes_notified == 1
        assert result.emails_sent == 0
        assert result.emails_failed == 1
        assert len(result.errors) == 1
        assert "Error sending alert" in result.errors[0]
        
        # Verify EmailAlert was still created for failed attempt
        alert_engine.email_alert_repo.create.assert_called_once()
        alert_data = alert_engine.email_alert_repo.create.call_args[0][0]
        assert alert_data['status'] == "failed"
        assert alert_data['error_message'] is not None
    
    async def test_send_alerts_for_change_policy_change_not_found(self, alert_engine):
        """Test that ValueError is raised when policy change not found."""
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="PolicyChange.*not found"):
            await alert_engine.send_alerts_for_change(uuid.uuid4())
    
    async def test_send_alerts_for_change_source_not_found(
        self, alert_engine, sample_policy_change
    ):
        """Test that ValueError is raised when source not found."""
        alert_engine.policy_change_repo.get_by_id = AsyncMock(return_value=sample_policy_change)
        alert_engine.source_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Source.*not found"):
            await alert_engine.send_alerts_for_change(sample_policy_change.id)

