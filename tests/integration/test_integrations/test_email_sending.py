"""Integration tests for email sending via Resend API.

These tests require a valid RESEND_API_KEY environment variable and will
send real emails to a test address. Use a test Resend account for these tests.

To run these tests:
1. Set RESEND_API_KEY environment variable
2. Set TEST_EMAIL_RECIPIENT environment variable (test email address)
3. Run: pytest tests/integration/test_integrations/test_email_sending.py -v

Note: These tests are skipped if RESEND_API_KEY is not set.
"""

import pytest
import os
from api.integrations.resend import ResendEmailService, create_email_service


# Skip all tests in this module if RESEND_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("RESEND_API_KEY"),
    reason="RESEND_API_KEY environment variable not set"
)


@pytest.fixture
def test_email_recipient():
    """Get test email recipient from environment variable."""
    recipient = os.getenv("TEST_EMAIL_RECIPIENT")
    if not recipient:
        pytest.skip("TEST_EMAIL_RECIPIENT environment variable not set")
    return recipient


@pytest.fixture
def email_service():
    """Create ResendEmailService instance for integration testing."""
    api_key = os.getenv("RESEND_API_KEY")
    from_address = os.getenv("EMAIL_FROM_ADDRESS", "onboarding@resend.dev")
    
    return ResendEmailService(api_key=api_key, from_address=from_address)


@pytest.mark.asyncio
class TestEmailSendingIntegration:
    """Integration tests for email sending via Resend API."""
    
    async def test_send_email_success(self, email_service, test_email_recipient):
        """Test sending a real email via Resend API."""
        result = email_service.send_email(
            recipient=test_email_recipient,
            subject="Test Email - Policy Aggregator Integration Test",
            html_body="""
            <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a test email from Policy Aggregator integration tests.</p>
                <p>If you received this, the email integration is working correctly.</p>
            </body>
            </html>
            """,
            text_body="""
            Test Email
            
            This is a test email from Policy Aggregator integration tests.
            If you received this, the email integration is working correctly.
            """
        )
        
        assert result.success is True, f"Email send failed: {result.error}"
        assert result.message_id is not None
        assert result.error is None
    
    async def test_send_email_with_html_and_text(self, email_service, test_email_recipient):
        """Test sending email with both HTML and plain text versions."""
        html_body = """
        <html>
        <body>
            <h1>Policy Change Alert</h1>
            <p>Route: IN → DE, Student Visa</p>
            <p>Source: Germany BMI</p>
            <p>This is a test of the email template system.</p>
        </body>
        </html>
        """
        
        text_body = """
        Policy Change Alert
        
        Route: IN → DE, Student Visa
        Source: Germany BMI
        This is a test of the email template system.
        """
        
        result = email_service.send_email(
            recipient=test_email_recipient,
            subject="Test Email - HTML and Text Versions",
            html_body=html_body,
            text_body=text_body
        )
        
        assert result.success is True
        assert result.message_id is not None
    
    async def test_send_email_invalid_recipient(self, email_service):
        """Test that invalid email address is rejected."""
        result = email_service.send_email(
            recipient="invalid-email-address",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        
        assert result.success is False
        assert "Invalid email address format" in result.error
    
    async def test_send_email_invalid_api_key(self):
        """Test that invalid API key returns error."""
        service = ResendEmailService(api_key="invalid_key", from_address="test@example.com")
        
        result = service.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test"
        )
        
        # Should fail with authentication error (401)
        assert result.success is False
        # Error should indicate authentication failure
        assert result.error is not None
    
    async def test_email_service_abstraction(self, test_email_recipient):
        """Test that email service abstraction works."""
        api_key = os.getenv("RESEND_API_KEY")
        from_address = os.getenv("EMAIL_FROM_ADDRESS", "onboarding@resend.dev")
        
        service = create_email_service("resend", api_key=api_key, from_address=from_address)
        
        result = service.send_email(
            recipient=test_email_recipient,
            subject="Test Email - Abstraction Layer",
            html_body="<html><body>Test</body></html>",
            text_body="Test"
        )
        
        assert result.success is True
        assert result.message_id is not None

