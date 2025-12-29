"""Resend email service integration.

This module provides an abstraction layer for sending emails via Resend API,
with error handling, retry logic, rate limiting, and comprehensive logging.
"""

import logging
import time
import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

try:
    from resend import Resend
    try:
        from resend.exceptions import ResendError
    except ImportError:
        # Fallback for different Resend SDK versions
        class ResendError(Exception):
            """Resend API error."""
            def __init__(self, message, status_code=None):
                super().__init__(message)
                self.status_code = status_code
except ImportError:
    Resend = None
    ResendError = Exception

from api.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Result of email send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailServiceError(Exception):
    """Base exception for email service errors."""
    pass


class EmailValidationError(EmailServiceError):
    """Exception for invalid email addresses."""
    pass


class EmailRateLimitError(EmailServiceError):
    """Exception for rate limit exceeded."""
    pass


class EmailService:
    """Abstract base class for email service providers."""
    
    def send_email(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> EmailResult:
        """
        Send an email.
        
        Args:
            recipient: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text email body
            
        Returns:
            EmailResult with success status and message ID
        """
        raise NotImplementedError


class ResendEmailService(EmailService):
    """Resend email service implementation."""
    
    # Rate limiting constants
    FREE_TIER_DAILY_LIMIT = 100
    FREE_TIER_MONTHLY_LIMIT = 3000
    
    def __init__(self, api_key: Optional[str] = None, from_address: Optional[str] = None):
        """
        Initialize Resend email service.
        
        Args:
            api_key: Resend API key (defaults to RESEND_API_KEY from config)
            from_address: From email address (defaults to EMAIL_FROM_ADDRESS from config)
            
        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or settings.RESEND_API_KEY
        self.from_address = from_address or settings.EMAIL_FROM_ADDRESS
        
        if not self.api_key:
            raise ValueError("Resend API key is required. Set RESEND_API_KEY environment variable.")
        
        if Resend is None:
            raise ImportError("Resend SDK not installed. Install with: pip install resend")
        
        self.client = Resend(api_key=self.api_key)
        
        # Rate limiting tracking
        self._daily_email_count = 0
        self._daily_reset_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self._monthly_email_count = 0
        self._monthly_reset_time = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)
        self._monthly_reset_time = self._monthly_reset_time.replace(day=1)
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email address for logging (privacy).
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email (e.g., "u***@example.com")
        """
        if '@' not in email:
            return "***"
        local, domain = email.split('@', 1)
        if len(local) > 1:
            masked_local = local[0] + '*' * (len(local) - 1)
        else:
            masked_local = '*'
        return f"{masked_local}@{domain}"
    
    def _check_rate_limits(self) -> None:
        """
        Check and update rate limit tracking.
        
        Raises:
            EmailRateLimitError: If rate limit exceeded
        """
        now = datetime.utcnow()
        
        # Reset daily count if needed
        if now >= self._daily_reset_time:
            self._daily_email_count = 0
            self._daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Reset monthly count if needed
        if now >= self._monthly_reset_time:
            self._monthly_email_count = 0
            next_month = now.replace(day=1) + timedelta(days=32)
            self._monthly_reset_time = next_month.replace(day=1)
        
        # Check daily limit
        if self._daily_email_count >= self.FREE_TIER_DAILY_LIMIT:
            logger.warning(
                f"Daily email limit reached: {self._daily_email_count}/{self.FREE_TIER_DAILY_LIMIT}"
            )
            raise EmailRateLimitError(
                f"Daily email limit exceeded: {self._daily_email_count}/{self.FREE_TIER_DAILY_LIMIT}"
            )
        
        # Check monthly limit
        if self._monthly_email_count >= self.FREE_TIER_MONTHLY_LIMIT:
            logger.warning(
                f"Monthly email limit reached: {self._monthly_email_count}/{self.FREE_TIER_MONTHLY_LIMIT}"
            )
            raise EmailRateLimitError(
                f"Monthly email limit exceeded: {self._monthly_email_count}/{self.FREE_TIER_MONTHLY_LIMIT}"
            )
        
        # Log warning if approaching limit
        if self._daily_email_count >= self.FREE_TIER_DAILY_LIMIT * 0.8:
            logger.warning(
                f"Approaching daily email limit: {self._daily_email_count}/{self.FREE_TIER_DAILY_LIMIT}"
            )
    
    def _increment_rate_limit(self) -> None:
        """Increment rate limit counters."""
        self._daily_email_count += 1
        self._monthly_email_count += 1
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Determine if an error is transient (should be retried).
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is transient, False otherwise
        """
        # Network errors are transient
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # Check ResendError for status codes
        if isinstance(error, ResendError):
            # 5xx errors are transient
            status_code = getattr(error, 'status_code', None)
            if status_code and status_code >= 500:
                return True
            # 429 (rate limit) might be transient if we're not actually over limit
            if status_code == 429:
                return True
        
        return False
    
    def _is_permanent_error(self, error: Exception) -> bool:
        """
        Determine if an error is permanent (should not be retried).
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is permanent, False otherwise
        """
        # Check ResendError for status codes
        if isinstance(error, ResendError):
            # 400, 401, 403 are permanent
            status_code = getattr(error, 'status_code', None)
            if status_code and status_code in (400, 401, 403):
                return True
        
        return False
    
    def send_email(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
        max_retries: int = 3
    ) -> EmailResult:
        """
        Send an email with retry logic.
        
        Args:
            recipient: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text email body
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            EmailResult with success status and message ID
        """
        # Validate email format
        if not self._validate_email(recipient):
            error_msg = f"Invalid email address format: {recipient}"
            logger.error(error_msg)
            return EmailResult(
                success=False,
                error=error_msg
            )
        
        # Check rate limits
        try:
            self._check_rate_limits()
        except EmailRateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            return EmailResult(
                success=False,
                error=str(e)
            )
        
        masked_email = self._mask_email(recipient)
        logger.info(f"Attempting to send email to {masked_email} | Subject: {subject[:50]}...")
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                # Send email via Resend API
                response = self.client.emails.send(
                    from_=self.from_address,
                    to=[recipient],
                    subject=subject,
                    html=html_body,
                    text=text_body
                )
                
                # Extract message ID from response
                message_id = response.get('id') if isinstance(response, dict) else None
                
                # Increment rate limit counters
                self._increment_rate_limit()
                
                logger.info(
                    f"Email sent successfully to {masked_email} | "
                    f"Message ID: {message_id} | "
                    f"Subject: {subject[:50]}..."
                )
                
                return EmailResult(
                    success=True,
                    message_id=message_id
                )
                
            except EmailRateLimitError as e:
                # Rate limit error - don't retry
                logger.error(f"Rate limit exceeded: {e}")
                return EmailResult(
                    success=False,
                    error=str(e)
                )
                
            except EmailValidationError as e:
                # Validation error - don't retry
                logger.error(f"Email validation error: {e}")
                return EmailResult(
                    success=False,
                    error=str(e)
                )
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check if error is permanent (don't retry)
                if self._is_permanent_error(e):
                    logger.error(
                        f"Permanent error sending email to {masked_email} | "
                        f"Error: {error_type}: {error_msg}"
                    )
                    return EmailResult(
                        success=False,
                        error=f"{error_type}: {error_msg}"
                    )
                
                # Check if error is transient (retry)
                if self._is_transient_error(e):
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        backoff_time = 2 ** attempt
                        logger.warning(
                            f"Transient error sending email to {masked_email} (attempt {attempt + 1}/{max_retries}) | "
                            f"Error: {error_type}: {error_msg} | "
                            f"Retrying in {backoff_time}s..."
                        )
                        time.sleep(backoff_time)
                        continue
                    else:
                        logger.error(
                            f"Failed to send email to {masked_email} after {max_retries} attempts | "
                            f"Error: {error_type}: {error_msg}"
                        )
                else:
                    # Unknown error - don't retry
                    logger.error(
                        f"Error sending email to {masked_email} | "
                        f"Error: {error_type}: {error_msg}"
                    )
                    return EmailResult(
                        success=False,
                        error=f"{error_type}: {error_msg}"
                    )
        
        # All retries exhausted
        error_msg = f"Failed after {max_retries} attempts: {str(last_error)}"
        logger.error(f"Failed to send email to {masked_email} | {error_msg}")
        return EmailResult(
            success=False,
            error=error_msg
        )


# Factory function to create email service instance
def create_email_service(
    provider: str = "resend",
    api_key: Optional[str] = None,
    from_address: Optional[str] = None
) -> EmailService:
    """
    Create an email service instance.
    
    Args:
        provider: Email service provider ("resend" is currently supported)
        api_key: API key (defaults to config)
        from_address: From email address (defaults to config)
        
    Returns:
        EmailService instance
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider.lower() == "resend":
        return ResendEmailService(api_key=api_key, from_address=from_address)
    else:
        raise ValueError(f"Unsupported email provider: {provider}")


# Default email service instance (lazy initialization)
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get the default email service instance.
    
    Returns:
        EmailService instance
        
    Raises:
        ValueError: If email service cannot be initialized
    """
    global _email_service
    if _email_service is None:
        _email_service = create_email_service()
    return _email_service

