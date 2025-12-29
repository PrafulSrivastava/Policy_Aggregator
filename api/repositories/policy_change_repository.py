"""Repository for PolicyChange model."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from api.models.db.policy_change import PolicyChange
from api.models.db.source import Source


class PolicyChangeRepository:
    """Repository for PolicyChange database operations.
    
    Note: PolicyChange records are immutable - no update method provided.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(self, change_data: dict) -> PolicyChange:
        """
        Create a new PolicyChange.
        
        Args:
            change_data: Dictionary with change fields
            
        Returns:
            Created PolicyChange instance
        """
        change = PolicyChange(**change_data)
        self.session.add(change)
        await self.session.commit()
        await self.session.refresh(change)
        return change
    
    async def get_by_id(self, change_id: uuid.UUID) -> Optional[PolicyChange]:
        """
        Get PolicyChange by ID.
        
        Args:
            change_id: PolicyChange UUID
            
        Returns:
            PolicyChange instance or None if not found
        """
        result = await self.session.execute(
            select(PolicyChange).where(PolicyChange.id == change_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_source_id(self, source_id: uuid.UUID) -> List[PolicyChange]:
        """
        Get all PolicyChanges for a source, ordered by detected_at descending.
        
        Args:
            source_id: Source UUID
            
        Returns:
            List of PolicyChange instances for the source
        """
        result = await self.session.execute(
            select(PolicyChange)
            .where(PolicyChange.source_id == source_id)
            .order_by(desc(PolicyChange.detected_at))
        )
        return list(result.scalars().all())
    
    async def get_latest_by_source_id(self, source_id: uuid.UUID) -> Optional[PolicyChange]:
        """
        Get the latest PolicyChange for a source.
        
        Args:
            source_id: Source UUID
            
        Returns:
            Latest PolicyChange instance or None if no changes exist
        """
        result = await self.session.execute(
            select(PolicyChange)
            .where(PolicyChange.source_id == source_id)
            .order_by(desc(PolicyChange.detected_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_route(
        self,
        origin: str,
        destination: str,
        visa_type: str
    ) -> List[PolicyChange]:
        """
        Get PolicyChanges for sources matching a route (origin → destination, visa type).
        
        This finds all sources matching the route criteria, then returns changes for those sources.
        
        Args:
            origin: Origin country code (2 characters)
            destination: Destination country code (2 characters)
            visa_type: Visa type string
            
        Returns:
            List of PolicyChange instances matching the route
        """
        # Find sources matching the route
        sources_result = await self.session.execute(
            select(Source)
            .where(Source.country == destination.upper())
            .where(Source.visa_type == visa_type)
            .where(Source.is_active == True)
        )
        sources = list(sources_result.scalars().all())
        
        if not sources:
            return []
        
        source_ids = [source.id for source in sources]
        
        # Get changes for matching sources
        result = await self.session.execute(
            select(PolicyChange)
            .where(PolicyChange.source_id.in_(source_ids))
            .order_by(desc(PolicyChange.detected_at))
        )
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[PolicyChange]:
        """
        Get PolicyChanges within a date range.
        
        Args:
            start_date: Start datetime (inclusive)
            end_date: End datetime (inclusive)
            
        Returns:
            List of PolicyChange instances within the date range
        """
        result = await self.session.execute(
            select(PolicyChange)
            .where(
                and_(
                    PolicyChange.detected_at >= start_date,
                    PolicyChange.detected_at <= end_date
                )
            )
            .order_by(desc(PolicyChange.detected_at))
        )
        return list(result.scalars().all())
    
    async def get_change_with_formatted_diff(
        self,
        change_id: uuid.UUID
    ) -> Optional[PolicyChange]:
        """
        Get PolicyChange by ID with formatted diff ready for display.
        
        The diff is already stored in unified diff format which is human-readable.
        This method retrieves the PolicyChange and ensures the diff is ready for display.
        
        Args:
            change_id: PolicyChange UUID
            
        Returns:
            PolicyChange instance with diff ready for display, or None if not found
        """
        change = await self.get_by_id(change_id)
        
        if change is None:
            return None
        
        # Diff is already in unified diff format (human-readable)
        # No additional formatting needed - it's ready for display
        # Future: Could add HTML formatting here if needed
        return change

