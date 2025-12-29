"""Unit tests for Resend email service integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from api.integrations.resend import (
    ResendEmailService,
    EmailResult,
    EmailServiceError,
    EmailValidationError,
    EmailRateLimitError,
    create_email_service,
    get_email_service
)


@pytest.fixture
def mock_resend_client():
    """Mock Resend client."""
    with patch('api.integrations.resend.Resend') as mock_resend:
        mock_client = MagicMock()
        mock_resend.return_value = mock_client
        yield mock_client


@pytest.fixture
def email_service(mock_resend_client):
    """Create ResendEmailService instance for testing."""
    with patch('api.integrations.resend.settings') as mock_settings:
        mock_settings.RESEND_API_KEY = "test_api_key"
        mock_settings.EMAIL_FROM_ADDRESS = "test@example.com"
        service = ResendEmailService()
        service.client = mock_resend_client
        return service


class TestResendEmailService:
    """Tests for ResendEmailService."""
    
    def test_init_requires_api_key(self):
        """Test that initialization requires API key."""
        with patch('api.integrations.resend.settings') as mock_settings:
            mock_settings.RESEND_API_KEY = None
            with pytest.raises(ValueError, match="Resend API key is required"):
                ResendEmailService()
    
    def test_init_creates_resend_client(self, mock_resend_client):
        """Test that Resend client is created on initialization."""
        with patch('api.integrations.resend.settings') as mock_settings:
            mock_settings.RESEND_API_KEY = "test_api_key"
            mock_settings.EMAIL_FROM_ADDRESS = "test@example.com"
            service = ResendEmailService()
            assert service.client is not None
    
    def test_send_email_success(self, email_service, mock_resend_client):
        """Test successful email send."""
        mock_resend_client.emails.send.return_value = {"id": "email_123"}
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        
        assert result.success is True
        assert result.message_id == "email_123"
        assert result.error is None
        mock_resend_client.emails.send.assert_called_once()
    
    def test_send_email_invalid_email_format(self, email_service):
        """Test that invalid email format is rejected."""
        result = email_service.send_email(
            recipient="invalid-email",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        
        assert result.success is False
        assert "Invalid email address format" in result.error
    
    def test_send_email_handles_network_error_with_retry(self, email_service, mock_resend_client):
        """Test that network errors are retried."""
        # First two attempts fail with ConnectionError, third succeeds
        mock_resend_client.emails.send.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            {"id": "email_123"}
        ]
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
            max_retries=3
        )
        
        assert result.success is True
        assert result.message_id == "email_123"
        assert mock_resend_client.emails.send.call_count == 3
    
    def test_send_email_handles_timeout_error_with_retry(self, email_service, mock_resend_client):
        """Test that timeout errors are retried."""
        mock_resend_client.emails.send.side_effect = [
            TimeoutError("Timeout"),
            {"id": "email_123"}
        ]
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
            max_retries=2
        )
        
        assert result.success is True
        assert result.message_id == "email_123"
    
    def test_send_email_handles_500_error_with_retry(self, email_service, mock_resend_client):
        """Test that 5xx errors are retried."""
        # Mock ResendError with 500 status
        error_500 = Exception("Server error")
        error_500.status_code = 500
        
        mock_resend_client.emails.send.side_effect = [
            error_500,
            {"id": "email_123"}
        ]
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
            max_retries=2
        )
        
        assert result.success is True
        assert result.message_id == "email_123"
    
    def test_send_email_handles_401_error_no_retry(self, email_service, mock_resend_client):
        """Test that 401 errors are not retried."""
        # Mock ResendError with 401 status
        error_401 = Exception("Unauthorized")
        error_401.status_code = 401
        
        mock_resend_client.emails.send.side_effect = error_401
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
            max_retries=3
        )
        
        assert result.success is False
        assert "401" in result.error or "Unauthorized" in result.error
        # Should not retry permanent errors
        assert mock_resend_client.emails.send.call_count == 1
    
    def test_send_email_handles_400_error_no_retry(self, email_service, mock_resend_client):
        """Test that 400 errors are not retried."""
        # Mock ResendError with 400 status
        error_400 = Exception("Bad request")
        error_400.status_code = 400
        
        mock_resend_client.emails.send.side_effect = error_400
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
            max_retries=3
        )
        
        assert result.success is False
        # Should not retry permanent errors
        assert mock_resend_client.emails.send.call_count == 1
    
    def test_send_email_exhausts_retries(self, email_service, mock_resend_client):
        """Test that all retries are exhausted before failing."""
        mock_resend_client.emails.send.side_effect = ConnectionError("Network error")
        
        result = email_service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
            max_retries=3
        )
        
        assert result.success is False
        assert "Failed after 3 attempts" in result.error
        assert mock_resend_client.emails.send.call_count == 3
    
    def test_validate_email_valid_formats(self, email_service):
        """Test email validation with valid formats."""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "user123@example-domain.com"
        ]
        
        for email in valid_emails:
            assert email_service._validate_email(email) is True
    
    def test_validate_email_invalid_formats(self, email_service):
        """Test email validation with invalid formats."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            ""
        ]
        
        for email in invalid_emails:
            assert email_service._validate_email(email) is False
    
    def test_mask_email_privacy(self, email_service):
        """Test that email masking works for privacy."""
        masked = email_service._mask_email("test@example.com")
        assert masked.startswith("t")
        assert "@example.com" in masked
        assert "test" not in masked or masked.count("*") > 0
    
    def test_rate_limit_tracking(self, email_service):
        """Test that rate limit tracking works."""
        # Reset counters
        email_service._daily_email_count = 0
        email_service._monthly_email_count = 0
        
        # Should not raise error when under limit
        email_service._check_rate_limits()
        
        # Set to limit
        email_service._daily_email_count = email_service.FREE_TIER_DAILY_LIMIT
        
        # Should raise error when at limit
        with pytest.raises(EmailRateLimitError):
            email_service._check_rate_limits()
    
    def test_rate_limit_reset_daily(self, email_service):
        """Test that daily rate limit resets."""
        email_service._daily_email_count = 50
        email_service._daily_reset_time = datetime.utcnow() - timedelta(hours=1)
        
        # Should reset and not raise error
        email_service._check_rate_limits()
        assert email_service._daily_email_count == 0
    
    def test_increment_rate_limit(self, email_service):
        """Test that rate limit counters are incremented."""
        initial_daily = email_service._daily_email_count
        initial_monthly = email_service._monthly_email_count
        
        email_service._increment_rate_limit()
        
        assert email_service._daily_email_count == initial_daily + 1
        assert email_service._monthly_email_count == initial_monthly + 1


class TestEmailServiceFactory:
    """Tests for email service factory functions."""
    
    def test_create_email_service_resend(self, mock_resend_client):
        """Test creating Resend email service."""
        with patch('api.integrations.resend.settings') as mock_settings:
            mock_settings.RESEND_API_KEY = "test_api_key"
            mock_settings.EMAIL_FROM_ADDRESS = "test@example.com"
            service = create_email_service("resend")
            assert isinstance(service, ResendEmailService)
    
    def test_create_email_service_unsupported(self):
        """Test that unsupported provider raises error."""
        with pytest.raises(ValueError, match="Unsupported email provider"):
            create_email_service("unsupported")
    
    def test_get_email_service_singleton(self, mock_resend_client):
        """Test that get_email_service returns singleton."""
        with patch('api.integrations.resend.settings') as mock_settings:
            mock_settings.RESEND_API_KEY = "test_api_key"
            mock_settings.EMAIL_FROM_ADDRESS = "test@example.com"
            
            # Reset singleton
            import api.integrations.resend as resend_module
            resend_module._email_service = None
            
            service1 = get_email_service()
            service2 = get_email_service()
            
            assert service1 is service2

