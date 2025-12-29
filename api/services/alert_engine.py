"""Alert engine service.

This service sends email alerts when policy changes are detected.
It matches policy changes to route subscriptions, formats email content,
and sends alerts via the email service.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.db.policy_change import PolicyChange
from api.models.db.route_subscription import RouteSubscription
from api.models.db.source import Source
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.source_repository import SourceRepository
from api.repositories.email_alert_repository import EmailAlertRepository
from api.services.route_mapper import RouteMapper
from api.services.email_template import EmailTemplateService
from api.integrations.resend import get_email_service, EmailService

logger = logging.getLogger(__name__)


@dataclass
class AlertResult:
    """Result of alert sending operation."""
    policy_change_id: uuid.UUID
    routes_notified: int
    emails_sent: int
    emails_failed: int
    errors: List[str]


class AlertEngine:
    """Service for sending email alerts when policy changes are detected."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize alert engine with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.policy_change_repo = PolicyChangeRepository(session)
        self.source_repo = SourceRepository(session)
        self.email_alert_repo = EmailAlertRepository(session)
        self.route_mapper = RouteMapper(session)
        self.email_template_service = EmailTemplateService()
        self.email_service = get_email_service()
    
    async def send_alerts_for_change(self, policy_change_id: uuid.UUID) -> AlertResult:
        """
        Send email alerts for a policy change.
        
        Flow:
        1. Get PolicyChange record
        2. Get Source from PolicyChange
        3. Find all RouteSubscriptions that match this source (via mapping logic)
        4. For each route subscription:
           - Format email content (use email template)
           - Send email (use email service)
           - Create EmailAlert record
        
        Args:
            policy_change_id: UUID of the policy change
            
        Returns:
            AlertResult with summary of alert sending operation
            
        Raises:
            ValueError: If policy change not found
        """
        logger.info(f"Sending alerts for policy change {policy_change_id}")
        
        # Get PolicyChange record
        policy_change = await self.policy_change_repo.get_by_id(policy_change_id)
        if not policy_change:
            raise ValueError(f"PolicyChange with id {policy_change_id} not found")
        
        # Get Source from PolicyChange
        source = await self.source_repo.get_by_id(policy_change.source_id)
        if not source:
            raise ValueError(f"Source with id {policy_change.source_id} not found")
        
        # Find matching RouteSubscriptions using route mapper
        routes = await self.route_mapper.get_routes_for_source(source)
        
        if not routes:
            logger.info(
                f"No matching routes found for policy change {policy_change_id} "
                f"(source: {source.country}, {source.visa_type})"
            )
            return AlertResult(
                policy_change_id=policy_change_id,
                routes_notified=0,
                emails_sent=0,
                emails_failed=0,
                errors=[]
            )
        
        logger.info(
            f"Found {len(routes)} matching route(s) for policy change {policy_change_id}"
        )
        
        # Track results
        emails_sent = 0
        emails_failed = 0
        errors: List[str] = []
        
        # For each route subscription, send email alert
        for route in routes:
            try:
                logger.info(
                    f"Sending alert to route {route.id}, email {route.email} "
                    f"for policy change {policy_change_id}"
                )
                
                # Render email template
                email_content = self.email_template_service.render_change_alert_template(
                    change=policy_change,
                    route=route,
                    source=source
                )
                
                # Send email via email service
                email_result = self.email_service.send_email(
                    recipient=route.email,
                    subject=email_content.subject,
                    html_body=email_content.html_body,
                    text_body=email_content.text_body
                )
                
                # Create EmailAlert record
                sent_at = datetime.utcnow()
                alert_data = {
                    "policy_change_id": policy_change.id,
                    "route_subscription_id": route.id,
                    "sent_at": sent_at,
                    "email_provider": "resend",
                    "email_provider_id": email_result.message_id,
                    "status": "sent" if email_result.success else "failed",
                    "error_message": email_result.error if not email_result.success else None
                }
                
                await self.email_alert_repo.create(alert_data)
                
                if email_result.success:
                    emails_sent += 1
                    logger.info(
                        f"Alert sent successfully to {route.email} "
                        f"(route {route.id}, message ID: {email_result.message_id})"
                    )
                else:
                    emails_failed += 1
                    error_msg = f"Failed to send alert to {route.email}: {email_result.error}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                # Handle errors gracefully - continue with other routes
                emails_failed += 1
                error_msg = f"Error sending alert to route {route.id} ({route.email}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                
                # Still create EmailAlert record for failed attempt
                try:
                    sent_at = datetime.utcnow()
                    alert_data = {
                        "policy_change_id": policy_change.id,
                        "route_subscription_id": route.id,
                        "sent_at": sent_at,
                        "email_provider": "resend",
                        "email_provider_id": None,
                        "status": "failed",
                        "error_message": str(e)
                    }
                    await self.email_alert_repo.create(alert_data)
                except Exception as alert_error:
                    logger.error(
                        f"Failed to create EmailAlert record for route {route.id}: {alert_error}",
                        exc_info=True
                    )
        
        # Log summary
        logger.info(
            f"Sent {emails_sent} alert(s) for policy change {policy_change_id} "
            f"({emails_failed} failed)"
        )
        
        return AlertResult(
            policy_change_id=policy_change_id,
            routes_notified=len(routes),
            emails_sent=emails_sent,
            emails_failed=emails_failed,
            errors=errors
        )

