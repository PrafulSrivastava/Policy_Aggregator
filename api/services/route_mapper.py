"""Route-to-source mapping service.

This service provides logic to map route subscriptions to relevant sources
and vice versa, enabling the system to determine which sources to monitor
for each route subscription.
"""

import logging
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.db.route_subscription import RouteSubscription
from api.models.db.source import Source
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository

logger = logging.getLogger(__name__)


class RouteMapper:
    """Service for mapping routes to sources and vice versa."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize route mapper with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.route_repo = RouteSubscriptionRepository(session)
    
    async def get_sources_for_route(
        self,
        route_subscription: RouteSubscription
    ) -> List[Source]:
        """
        Get all active sources that match a route subscription.
        
        Mapping logic:
        - Match sources by destination_country (route.destination_country == source.country)
        - Match sources by visa_type (route.visa_type == source.visa_type)
        - Only return active sources (is_active == True)
        
        Args:
            route_subscription: RouteSubscription instance to find sources for
            
        Returns:
            List of matching active Source instances
            
        Note:
            Logs a warning if no matching sources are found.
        """
        sources = await self.source_repo.get_active_by_country_visa(
            country=route_subscription.destination_country,
            visa_type=route_subscription.visa_type
        )
        
        if not sources:
            logger.warning(
                f"No matching sources found for route {route_subscription.id} "
                f"(destination={route_subscription.destination_country}, "
                f"visa_type={route_subscription.visa_type})"
            )
        
        return sources
    
    async def get_routes_for_source(self, source: Source) -> List[RouteSubscription]:
        """
        Get all active route subscriptions that match a source.
        
        Reverse mapping: finds all routes that would be affected by a source change.
        Matches routes where:
        - destination_country == source.country
        - visa_type == source.visa_type
        - is_active == True
        
        Args:
            source: Source instance to find routes for
            
        Returns:
            List of matching active RouteSubscription instances
        """
        routes = await self.route_repo.get_active_by_destination_visa(
            destination=source.country,
            visa_type=source.visa_type
        )
        
        return routes
    
    async def get_sources_for_route_id(self, route_id: uuid.UUID) -> List[Source]:
        """
        Get all active sources for a route subscription by ID.
        
        Helper function that loads the route subscription and then finds matching sources.
        
        Args:
            route_id: UUID of the route subscription
            
        Returns:
            List of matching active Source instances
            
        Raises:
            ValueError: If route subscription not found
        """
        route = await self.route_repo.get_by_id(route_id)
        if not route:
            raise ValueError(f"RouteSubscription with id {route_id} not found")
        
        return await self.get_sources_for_route(route)

