"""Integration tests for route-to-source mapping."""

import pytest
from api.services.route_mapper import RouteMapper
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository


@pytest.mark.asyncio
class TestRouteMappingIntegration:
    """Integration tests for route-to-source mapping."""
    
    async def test_create_routes_and_sources_verify_mappings(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: create routes and sources, verify mappings."""
        # Create source: country="DE", visa_type="Student"
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create route: destination="DE", visa_type="Student"
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Verify route maps to source
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        assert len(sources) == 1
        assert sources[0].id == source.id
        assert sources[0].country == "DE"
        assert sources[0].visa_type == "Student"
        
        # Verify source maps to route
        routes = await mapper.get_routes_for_source(source)
        assert len(routes) == 1
        assert routes[0].id == route.id
        assert routes[0].destination_country == "DE"
        assert routes[0].visa_type == "Student"
    
    async def test_multiple_routes_match_one_source(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: multiple routes match one source."""
        # Create one source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create multiple routes with same destination/visa_type but different origins/emails
        route_repo = RouteSubscriptionRepository(db_session)
        
        route1_data = sample_route_subscription_data.copy()
        route1_data["origin_country"] = "IN"
        route1_data["email"] = "user1@example.com"
        route1 = await route_repo.create(route1_data)
        
        route2_data = sample_route_subscription_data.copy()
        route2_data["origin_country"] = "US"
        route2_data["email"] = "user2@example.com"
        route2 = await route_repo.create(route2_data)
        
        route3_data = sample_route_subscription_data.copy()
        route3_data["origin_country"] = "GB"
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
        route_ids = {r.id for r in routes}
        assert route1.id in route_ids
        assert route2.id in route_ids
        assert route3.id in route_ids
    
    async def test_multiple_sources_match_one_route(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: multiple sources match one route."""
        # Create one route
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create multiple sources with same country/visa_type but different URLs
        source_repo = SourceRepository(db_session)
        
        source1 = await source_repo.create(sample_source_data)
        
        source2_data = sample_source_data.copy()
        source2_data["url"] = "https://example.com/student-visa-alt1"
        source2_data["name"] = "Germany Student Visa Alternative 1"
        source2 = await source_repo.create(source2_data)
        
        source3_data = sample_source_data.copy()
        source3_data["url"] = "https://example.com/student-visa-alt2"
        source3_data["name"] = "Germany Student Visa Alternative 2"
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
    
    async def test_route_with_no_matching_sources(
        self, db_session, sample_route_subscription_data
    ):
        """Test: route with no matching sources."""
        # Create route
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create source with different country/visa_type (won't match)
        source_repo = SourceRepository(db_session)
        source_data = {
            "country": "FR",  # Different country
            "visa_type": "Work",  # Different visa type
            "url": "https://example.com/france-work",
            "name": "France Work Visa",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        await source_repo.create(source_data)
        
        # Route should not map to any sources
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        
        assert len(sources) == 0
    
    async def test_source_with_no_matching_routes(
        self, db_session, sample_source_data
    ):
        """Test: source with no matching routes."""
        # Create source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create route with different destination/visa_type (won't match)
        route_repo = RouteSubscriptionRepository(db_session)
        route_data = {
            "origin_country": "IN",
            "destination_country": "FR",  # Different country
            "visa_type": "Work",  # Different visa type
            "email": "test@example.com",
            "is_active": True
        }
        await route_repo.create(route_data)
        
        # Source should not map to any routes (but still monitored)
        mapper = RouteMapper(db_session)
        routes = await mapper.get_routes_for_source(source)
        
        assert len(routes) == 0
    
    async def test_inactive_sources_and_routes_not_matched(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: inactive sources and routes are not included in mappings."""
        source_repo = SourceRepository(db_session)
        route_repo = RouteSubscriptionRepository(db_session)
        
        # Create active source and route
        active_source = await source_repo.create(sample_source_data)
        active_route = await route_repo.create(sample_route_subscription_data)
        
        # Create inactive source with same country/visa_type
        inactive_source_data = sample_source_data.copy()
        inactive_source_data["is_active"] = False
        inactive_source_data["url"] = "https://example.com/inactive"
        inactive_source = await source_repo.create(inactive_source_data)
        
        # Create inactive route with same destination/visa_type
        inactive_route_data = sample_route_subscription_data.copy()
        inactive_route_data["is_active"] = False
        inactive_route_data["email"] = "inactive@example.com"
        inactive_route = await route_repo.create(inactive_route_data)
        
        mapper = RouteMapper(db_session)
        
        # Active route should only map to active source
        sources = await mapper.get_sources_for_route(active_route)
        assert len(sources) == 1
        assert sources[0].id == active_source.id
        
        # Active source should only map to active route
        routes = await mapper.get_routes_for_source(active_source)
        assert len(routes) == 1
        assert routes[0].id == active_route.id
        
        # Inactive route should not map to any sources
        inactive_sources = await mapper.get_sources_for_route(inactive_route)
        assert len(inactive_sources) == 0
        
        # Inactive source should not map to any routes
        inactive_routes = await mapper.get_routes_for_source(inactive_source)
        assert len(inactive_routes) == 0

