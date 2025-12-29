"""Repository for RouteSubscription model."""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from api.models.db.route_subscription import RouteSubscription


class RouteSubscriptionRepository:
    """Repository for RouteSubscription database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(self, route_data: dict) -> RouteSubscription:
        """
        Create a new RouteSubscription.
        
        Args:
            route_data: Dictionary with route subscription fields
            
        Returns:
            Created RouteSubscription instance
        """
        route = RouteSubscription(**route_data)
        self.session.add(route)
        await self.session.commit()
        await self.session.refresh(route)
        return route
    
    async def get_by_id(self, route_id: uuid.UUID) -> Optional[RouteSubscription]:
        """
        Get RouteSubscription by ID.
        
        Args:
            route_id: RouteSubscription UUID
            
        Returns:
            RouteSubscription instance or None if not found
        """
        result = await self.session.execute(
            select(RouteSubscription).where(RouteSubscription.id == route_id)
        )
        return result.scalar_one_or_none()
    
    async def list_all(self) -> List[RouteSubscription]:
        """
        List all RouteSubscriptions.
        
        Returns:
            List of all RouteSubscription instances
        """
        result = await self.session.execute(
            select(RouteSubscription).order_by(RouteSubscription.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[RouteSubscription], int]:
        """
        List RouteSubscriptions with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (list of RouteSubscription instances, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(RouteSubscription)
        )
        total = count_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(RouteSubscription)
            .order_by(RouteSubscription.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        return list(result.scalars().all()), total
    
    async def list_active(self) -> List[RouteSubscription]:
        """
        List all active RouteSubscriptions.
        
        Returns:
            List of active RouteSubscription instances
        """
        result = await self.session.execute(
            select(RouteSubscription)
            .where(RouteSubscription.is_active == True)
            .order_by(RouteSubscription.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_route(
        self,
        origin: str,
        destination: str,
        visa_type: str
    ) -> List[RouteSubscription]:
        """
        Get RouteSubscriptions matching a route.
        
        Args:
            origin: Origin country code (2 characters)
            destination: Destination country code (2 characters)
            visa_type: Visa type string
            
        Returns:
            List of matching RouteSubscription instances
        """
        result = await self.session.execute(
            select(RouteSubscription)
            .where(RouteSubscription.origin_country == origin.upper())
            .where(RouteSubscription.destination_country == destination.upper())
            .where(RouteSubscription.visa_type == visa_type)
            .order_by(RouteSubscription.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update(self, route_id: uuid.UUID, update_data: dict) -> RouteSubscription:
        """
        Update a RouteSubscription.
        
        Args:
            route_id: RouteSubscription UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated RouteSubscription instance
            
        Raises:
            ValueError: If route subscription not found
        """
        route = await self.get_by_id(route_id)
        if not route:
            raise ValueError(f"RouteSubscription with id {route_id} not found")
        
        for key, value in update_data.items():
            if hasattr(route, key):
                setattr(route, key, value)
        
        await self.session.commit()
        await self.session.refresh(route)
        return route
    
    async def delete(self, route_id: uuid.UUID) -> bool:
        """
        Delete a RouteSubscription.
        
        Args:
            route_id: RouteSubscription UUID
            
        Returns:
            True if deleted, False if not found
        """
        route = await self.get_by_id(route_id)
        if not route:
            return False
        
        await self.session.delete(route)
        await self.session.commit()
        return True
    
    async def exists(
        self,
        origin: str,
        destination: str,
        visa_type: str,
        email: str
    ) -> bool:
        """
        Check if a RouteSubscription exists for the given route and email.
        
        Args:
            origin: Origin country code (2 characters)
            destination: Destination country code (2 characters)
            visa_type: Visa type string
            email: Email address
            
        Returns:
            True if subscription exists, False otherwise
        """
        result = await self.session.execute(
            select(RouteSubscription)
            .where(RouteSubscription.origin_country == origin.upper())
            .where(RouteSubscription.destination_country == destination.upper())
            .where(RouteSubscription.visa_type == visa_type)
            .where(RouteSubscription.email == email.lower())
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    async def get_active_by_destination_visa(
        self,
        destination: str,
        visa_type: str
    ) -> List[RouteSubscription]:
        """
        Get active RouteSubscriptions by destination country and visa type.
        
        Args:
            destination: Destination country code (2 characters)
            visa_type: Visa type string
            
        Returns:
            List of matching active RouteSubscription instances
        """
        result = await self.session.execute(
            select(RouteSubscription)
            .where(RouteSubscription.destination_country == destination.upper())
            .where(RouteSubscription.visa_type == visa_type)
            .where(RouteSubscription.is_active == True)
            .order_by(RouteSubscription.created_at.desc())
        )
        return list(result.scalars().all())

