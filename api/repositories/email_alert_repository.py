"""Repository for EmailAlert model."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from api.models.db.email_alert import EmailAlert


class EmailAlertRepository:
    """Repository for EmailAlert database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(self, alert_data: dict) -> EmailAlert:
        """
        Create a new EmailAlert.
        
        Args:
            alert_data: Dictionary with alert fields
            
        Returns:
            Created EmailAlert instance
        """
        alert = EmailAlert(**alert_data)
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
    
    async def get_by_id(self, alert_id: uuid.UUID) -> Optional[EmailAlert]:
        """
        Get EmailAlert by ID.
        
        Args:
            alert_id: EmailAlert UUID
            
        Returns:
            EmailAlert instance or None if not found
        """
        result = await self.session.execute(
            select(EmailAlert).where(EmailAlert.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_policy_change(self, policy_change_id: uuid.UUID) -> List[EmailAlert]:
        """
        Get all EmailAlerts for a policy change.
        
        Args:
            policy_change_id: PolicyChange UUID
            
        Returns:
            List of EmailAlert instances
        """
        result = await self.session.execute(
            select(EmailAlert)
            .where(EmailAlert.policy_change_id == policy_change_id)
            .order_by(desc(EmailAlert.sent_at))
        )
        return list(result.scalars().all())
    
    async def get_by_route_subscription(self, route_subscription_id: uuid.UUID) -> List[EmailAlert]:
        """
        Get all EmailAlerts for a route subscription.
        
        Args:
            route_subscription_id: RouteSubscription UUID
            
        Returns:
            List of EmailAlert instances
        """
        result = await self.session.execute(
            select(EmailAlert)
            .where(EmailAlert.route_subscription_id == route_subscription_id)
            .order_by(desc(EmailAlert.sent_at))
        )
        return list(result.scalars().all())
    
    async def list_all(self, limit: Optional[int] = None) -> List[EmailAlert]:
        """
        List all EmailAlerts.
        
        Args:
            limit: Optional limit on number of results
            
        Returns:
            List of EmailAlert instances
        """
        query = select(EmailAlert).order_by(desc(EmailAlert.sent_at))
        if limit:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_failed_alerts(self) -> List[EmailAlert]:
        """
        Get all failed EmailAlerts.
        
        Returns:
            List of failed EmailAlert instances
        """
        result = await self.session.execute(
            select(EmailAlert)
            .where(EmailAlert.status == "failed")
            .order_by(desc(EmailAlert.sent_at))
        )
        return list(result.scalars().all())

