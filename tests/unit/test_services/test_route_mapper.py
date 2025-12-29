"""Unit tests for route mapper service."""

import pytest
import uuid
from api.services.route_mapper import RouteMapper
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository


@pytest.mark.asyncio
class TestRouteMapper:
    """Tests for RouteMapper service."""
    
    async def test_get_sources_for_route_returns_matching_sources(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test that get_sources_for_route returns matching sources by country and visa_type."""
        # Create matching source and route
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create mapper and get sources
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        
        # Should return the matching source
        assert len(sources) == 1
        assert sources[0].id == source.id
        assert sources[0].country == route.destination_country
        assert sources[0].visa_type == route.visa_type
    
    async def test_get_sources_for_route_returns_empty_if_no_matches(
        self, db_session, sample_route_subscription_data
    ):
        """Test that get_sources_for_route returns empty list if no matches."""
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create mapper and get sources (no sources exist)
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        
        # Should return empty list
        assert len(sources) == 0
    
    async def test_get_sources_for_route_only_returns_active_sources(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test that get_sources_for_route only returns active sources."""
        source_repo = SourceRepository(db_session)
        
        # Create active source
        active_source = await source_repo.create(sample_source_data)
        
        # Create inactive source with same country/visa_type
        inactive_source_data = sample_source_data.copy()
        inactive_source_data["is_active"] = False
        inactive_source = await source_repo.create(inactive_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create mapper and get sources
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        
        # Should only return active source
        assert len(sources) == 1
        assert sources[0].id == active_source.id
        assert sources[0].is_active is True
    
    async def test_get_routes_for_source_returns_matching_routes(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test that get_routes_for_source returns matching routes by country and visa_type."""
        # Create matching source and route
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create mapper and get routes
        mapper = RouteMapper(db_session)
        routes = await mapper.get_routes_for_source(source)
        
        # Should return the matching route
        assert len(routes) == 1
        assert routes[0].id == route.id
        assert routes[0].destination_country == source.country
        assert routes[0].visa_type == source.visa_type
    
    async def test_get_routes_for_source_returns_empty_if_no_matches(
        self, db_session, sample_source_data
    ):
        """Test that get_routes_for_source returns empty list if no matches."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create mapper and get routes (no routes exist)
        mapper = RouteMapper(db_session)
        routes = await mapper.get_routes_for_source(source)
        
        # Should return empty list
        assert len(routes) == 0
    
    async def test_get_routes_for_source_only_returns_active_routes(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test that get_routes_for_source only returns active routes."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        
        # Create active route
        active_route = await route_repo.create(sample_route_subscription_data)
        
        # Create inactive route with same destination/visa_type
        inactive_route_data = sample_route_subscription_data.copy()
        inactive_route_data["is_active"] = False
        inactive_route_data["email"] = "inactive@example.com"
        inactive_route = await route_repo.create(inactive_route_data)
        
        # Create mapper and get routes
        mapper = RouteMapper(db_session)
        routes = await mapper.get_routes_for_source(source)
        
        # Should only return active route
        assert len(routes) == 1
        assert routes[0].id == active_route.id
        assert routes[0].is_active is True
    
    async def test_get_sources_for_route_id_loads_route_and_returns_sources(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test that get_sources_for_route_id loads route and returns matching sources."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create mapper and get sources by route ID
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route_id(route.id)
        
        # Should return matching source
        assert len(sources) == 1
        assert sources[0].id == source.id
    
    async def test_get_sources_for_route_id_raises_error_if_route_not_found(self, db_session):
        """Test that get_sources_for_route_id raises ValueError if route not found."""
        mapper = RouteMapper(db_session)
        non_existent_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match=f"RouteSubscription with id {non_existent_id} not found"):
            await mapper.get_sources_for_route_id(non_existent_id)
    
    async def test_route_with_no_matching_sources_returns_empty_list(
        self, db_session, sample_route_subscription_data
    ):
        """Test edge case: route with no matching sources returns empty list."""
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        
        # Should return empty list (no error)
        assert len(sources) == 0
        assert isinstance(sources, list)
    
    async def test_source_with_no_matching_routes_returns_empty_list(
        self, db_session, sample_source_data
    ):
        """Test edge case: source with no matching routes returns empty list."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        mapper = RouteMapper(db_session)
        routes = await mapper.get_routes_for_source(source)
        
        # Should return empty list (no error, source still monitored)
        assert len(routes) == 0
        assert isinstance(routes, list)
    
    async def test_many_to_many_relationship_multiple_routes_one_source(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test many-to-many: multiple routes can match one source."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        
        # Create multiple routes with same destination/visa_type
        route1 = await route_repo.create(sample_route_subscription_data)
        route2_data = sample_route_subscription_data.copy()
        route2_data["email"] = "user2@example.com"
        route2 = await route_repo.create(route2_data)
        route3_data = sample_route_subscription_data.copy()
        route3_data["email"] = "user3@example.com"
        route3 = await route_repo.create(route3_data)
        
        # All routes should map to the same source
        mapper = RouteMapper(db_session)
        
        sources1 = await mapper.get_sources_for_route(route1)
        sources2 = await mapper.get_sources_for_route(route2)
        sources3 = await mapper.get_sources_for_route(route3)
        
        assert len(sources1) == 1
        assert len(sources2) == 1
        assert len(sources3) == 1
        assert sources1[0].id == source.id
        assert sources2[0].id == source.id
        assert sources3[0].id == source.id
        
        # Source should map to all routes
        routes = await mapper.get_routes_for_source(source)
        assert len(routes) == 3
    
    async def test_many_to_many_relationship_multiple_sources_one_route(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test many-to-many: multiple sources can match one route."""
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        source_repo = SourceRepository(db_session)
        
        # Create multiple sources with same country/visa_type
        source1 = await source_repo.create(sample_source_data)
        source2_data = sample_source_data.copy()
        source2_data["url"] = "https://example.com/student-visa-2"
        source2_data["name"] = "Germany Student Visa Source 2"
        source2 = await source_repo.create(source2_data)
        source3_data = sample_source_data.copy()
        source3_data["url"] = "https://example.com/student-visa-3"
        source3_data["name"] = "Germany Student Visa Source 3"
        source3 = await source_repo.create(source3_data)
        
        # Route should map to all sources
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        
        assert len(sources) == 3
        source_ids = {s.id for s in sources}
        assert source1.id in source_ids
        assert source2.id in source_ids
        assert source3.id in source_ids
        
        # All sources should map to the route
        routes1 = await mapper.get_routes_for_source(source1)
        routes2 = await mapper.get_routes_for_source(source2)
        routes3 = await mapper.get_routes_for_source(source3)
        
        assert len(routes1) == 1
        assert len(routes2) == 1
        assert len(routes3) == 1
        assert routes1[0].id == route.id
        assert routes2[0].id == route.id
        assert routes3[0].id == route.id

