"""Error tracking service for monitoring source fetch and email delivery failures.

This service tracks consecutive failures per source and sends admin notifications
when failure thresholds are exceeded.
"""

import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.models.db.source import Source
from api.repositories.source_repository import SourceRepository
from api.integrations.resend import get_email_service, EmailService

logger = logging.getLogger(__name__)

# Failure threshold for admin notifications
FAILURE_THRESHOLD = 3


class ErrorTracker:
    """Service for tracking errors and sending admin notifications."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize error tracker with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.email_service: Optional[EmailService] = None
    
    def _get_email_service(self) -> Optional[EmailService]:
        """Get email service instance (lazy initialization)."""
        if self.email_service is None:
            try:
                self.email_service = get_email_service()
            except Exception as e:
                logger.warning(f"Failed to initialize email service: {e}")
                return None
        return self.email_service
    
    async def record_fetch_success(self, source_id: uuid.UUID) -> None:
        """
        Record successful fetch for a source (resets failure count).
        
        Args:
            source_id: Source UUID
        """
        try:
            source = await self.source_repo.get_by_id(source_id)
            if not source:
                logger.warning(f"Source {source_id} not found for error tracking")
                return
            
            # Reset fetch failure count
            if source.consecutive_fetch_failures > 0:
                logger.info(
                    f"Resetting fetch failure count for source {source_id} "
                    f"(was {source.consecutive_fetch_failures})"
                )
            
            update_data = {
                "consecutive_fetch_failures": 0,
                "last_fetch_error": None
            }
            await self.source_repo.update(source_id, update_data)
            
        except Exception as e:
            logger.error(f"Error recording fetch success for source {source_id}: {e}", exc_info=True)
    
    async def record_fetch_failure(
        self,
        source_id: uuid.UUID,
        error_message: str
    ) -> None:
        """
        Record fetch failure for a source and check threshold.
        
        Args:
            source_id: Source UUID
            error_message: Error message describing the failure
        """
        try:
            source = await self.source_repo.get_by_id(source_id)
            if not source:
                logger.warning(f"Source {source_id} not found for error tracking")
                return
            
            # Increment failure count
            new_failure_count = source.consecutive_fetch_failures + 1
            
            update_data = {
                "consecutive_fetch_failures": new_failure_count,
                "last_fetch_error": error_message[:500]  # Limit error message length
            }
            await self.source_repo.update(source_id, update_data)
            
            logger.warning(
                f"Recorded fetch failure for source {source_id} ({source.name}): "
                f"consecutive failures = {new_failure_count}"
            )
            
            # Check threshold and send notification if exceeded
            if await self.check_failure_threshold(source_id, "fetch"):
                await self._send_admin_notification(
                    source=source,
                    error_type="fetch",
                    failure_count=new_failure_count,
                    error_message=error_message
                )
            
        except Exception as e:
            logger.error(f"Error recording fetch failure for source {source_id}: {e}", exc_info=True)
    
    async def record_email_failure(
        self,
        source_id: uuid.UUID,
        error_message: str
    ) -> None:
        """
        Record email delivery failure for a source and check threshold.
        
        Args:
            source_id: Source UUID
            error_message: Error message describing the failure
        """
        try:
            source = await self.source_repo.get_by_id(source_id)
            if not source:
                logger.warning(f"Source {source_id} not found for error tracking")
                return
            
            # Increment failure count
            new_failure_count = source.consecutive_email_failures + 1
            
            update_data = {
                "consecutive_email_failures": new_failure_count,
                "last_email_error": error_message[:500]  # Limit error message length
            }
            await self.source_repo.update(source_id, update_data)
            
            logger.warning(
                f"Recorded email failure for source {source_id} ({source.name}): "
                f"consecutive failures = {new_failure_count}"
            )
            
            # Check threshold and send notification if exceeded
            if await self.check_failure_threshold(source_id, "email"):
                await self._send_admin_notification(
                    source=source,
                    error_type="email",
                    failure_count=new_failure_count,
                    error_message=error_message
                )
            
        except Exception as e:
            logger.error(f"Error recording email failure for source {source_id}: {e}", exc_info=True)
    
    async def check_failure_threshold(
        self,
        source_id: uuid.UUID,
        error_type: str
    ) -> bool:
        """
        Check if failure threshold is exceeded for a source.
        
        Args:
            source_id: Source UUID
            error_type: Type of error ("fetch" or "email")
            
        Returns:
            True if threshold exceeded, False otherwise
        """
        try:
            source = await self.source_repo.get_by_id(source_id)
            if not source:
                return False
            
            if error_type == "fetch":
                return source.consecutive_fetch_failures >= FAILURE_THRESHOLD
            elif error_type == "email":
                return source.consecutive_email_failures >= FAILURE_THRESHOLD
            else:
                logger.warning(f"Unknown error type: {error_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking failure threshold for source {source_id}: {e}", exc_info=True)
            return False
    
    async def _send_admin_notification(
        self,
        source: Source,
        error_type: str,
        failure_count: int,
        error_message: str
    ) -> None:
        """
        Send admin notification email when failure threshold is exceeded.
        
        Args:
            source: Source instance
            error_type: Type of error ("fetch" or "email")
            failure_count: Number of consecutive failures
            error_message: Error message
        """
        admin_email = settings.ADMIN_EMAIL
        if not admin_email:
            logger.warning(
                f"ADMIN_EMAIL not configured. Cannot send error notification for source {source.id}"
            )
            return
        
        email_service = self._get_email_service()
        if not email_service:
            logger.warning(
                f"Email service not available. Cannot send error notification for source {source.id}"
            )
            return
        
        try:
            # Format email subject
            if error_type == "fetch":
                subject = f"⚠️ Policy Aggregator: Source Fetch Failure Alert - {source.name}"
            else:
                subject = f"⚠️ Policy Aggregator: Email Delivery Failure Alert - {source.name}"
            
            # Format email body
            last_success = (
                source.last_checked_at.isoformat() if source.last_checked_at
                else "Never"
            )
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #d32f2f;">Policy Aggregator Error Alert</h2>
                
                <p><strong>Source Information:</strong></p>
                <ul>
                    <li><strong>Name:</strong> {source.name}</li>
                    <li><strong>URL:</strong> <a href="{source.url}">{source.url}</a></li>
                    <li><strong>Country:</strong> {source.country}</li>
                    <li><strong>Visa Type:</strong> {source.visa_type}</li>
                </ul>
                
                <p><strong>Error Details:</strong></p>
                <ul>
                    <li><strong>Error Type:</strong> {error_type.capitalize()}</li>
                    <li><strong>Consecutive Failures:</strong> {failure_count}</li>
                    <li><strong>Last Error:</strong> {error_message}</li>
                    <li><strong>Last Successful Fetch:</strong> {last_success}</li>
                </ul>
                
                <p style="color: #666; font-size: 0.9em;">
                    This is an automated notification. Please investigate the source configuration
                    or network connectivity issues.
                </p>
            </body>
            </html>
            """
            
            text_body = f"""
Policy Aggregator Error Alert

Source Information:
- Name: {source.name}
- URL: {source.url}
- Country: {source.country}
- Visa Type: {source.visa_type}

Error Details:
- Error Type: {error_type.capitalize()}
- Consecutive Failures: {failure_count}
- Last Error: {error_message}
- Last Successful Fetch: {last_success}

This is an automated notification. Please investigate the source configuration
or network connectivity issues.
            """.strip()
            
            # Send email
            result = email_service.send_email(
                recipient=admin_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if result.success:
                logger.info(
                    f"Admin notification sent for source {source.id} "
                    f"({error_type} failures: {failure_count})"
                )
            else:
                logger.error(
                    f"Failed to send admin notification for source {source.id}: {result.error}"
                )
                
        except Exception as e:
            logger.error(
                f"Error sending admin notification for source {source.id}: {e}",
                exc_info=True
            )

