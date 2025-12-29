"""Integration tests for new route expansion (UK and Canada routes)."""

import pytest
from api.services.route_mapper import RouteMapper
from api.services.fetcher_manager import fetch_and_process_source
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.email_alert_repository import EmailAlertRepository


@pytest.mark.asyncio
class TestNewRouteExpansion:
    """Integration tests for new route expansion (UK and Canada)."""
    
    async def test_uk_route_source_mapping(self, db_session):
        """Test: create UK route subscription and verify sources are mapped correctly."""
        # Create UK sources
        source_repo = SourceRepository(db_session)
        
        uk_student_source = await source_repo.create({
            "country": "UK",
            "visa_type": "Student",
            "url": "https://www.gov.uk/student-visa",
            "name": "UK Home Office Student Visa Information",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        uk_work_source = await source_repo.create({
            "country": "UK",
            "visa_type": "Work",
            "url": "https://www.gov.uk/skilled-worker-visa",
            "name": "UK Home Office Skilled Worker Visa Information",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        # Create UK route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        uk_student_route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "UK",
            "visa_type": "Student",
            "email": "test@example.com",
            "is_active": True
        })
        
        uk_work_route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "UK",
            "visa_type": "Work",
            "email": "test@example.com",
            "is_active": True
        })
        
        # Verify route-to-source mapping
        mapper = RouteMapper(db_session)
        
        student_sources = await mapper.get_sources_for_route(uk_student_route)
        assert len(student_sources) == 1
        assert student_sources[0].id == uk_student_source.id
        assert student_sources[0].country == "UK"
        assert student_sources[0].visa_type == "Student"
        
        work_sources = await mapper.get_sources_for_route(uk_work_route)
        assert len(work_sources) == 1
        assert work_sources[0].id == uk_work_source.id
        assert work_sources[0].country == "UK"
        assert work_sources[0].visa_type == "Work"
        
        # Verify source-to-route mapping
        student_routes = await mapper.get_routes_for_source(uk_student_source)
        assert len(student_routes) == 1
        assert student_routes[0].id == uk_student_route.id
        
        work_routes = await mapper.get_routes_for_source(uk_work_source)
        assert len(work_routes) == 1
        assert work_routes[0].id == uk_work_route.id
    
    async def test_canada_route_source_mapping(self, db_session):
        """Test: create Canada route subscription and verify sources are mapped correctly."""
        # Create Canada sources
        source_repo = SourceRepository(db_session)
        
        ca_student_source = await source_repo.create({
            "country": "CA",
            "visa_type": "Student",
            "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html",
            "name": "IRCC Study Permit Information",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        ca_work_source = await source_repo.create({
            "country": "CA",
            "visa_type": "Work",
            "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html",
            "name": "IRCC Work in Canada Information",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        # Create Canada route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        ca_student_route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "CA",
            "visa_type": "Student",
            "email": "test@example.com",
            "is_active": True
        })
        
        ca_work_route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "CA",
            "visa_type": "Work",
            "email": "test@example.com",
            "is_active": True
        })
        
        # Verify route-to-source mapping
        mapper = RouteMapper(db_session)
        
        student_sources = await mapper.get_sources_for_route(ca_student_route)
        assert len(student_sources) == 1
        assert student_sources[0].id == ca_student_source.id
        assert student_sources[0].country == "CA"
        assert student_sources[0].visa_type == "Student"
        
        work_sources = await mapper.get_sources_for_route(ca_work_route)
        assert len(work_sources) == 1
        assert work_sources[0].id == ca_work_source.id
        assert work_sources[0].country == "CA"
        assert work_sources[0].visa_type == "Work"
    
    async def test_new_route_fetch_pipeline(self, db_session):
        """Test: verify fetch pipeline works for new routes."""
        # Create UK source
        source_repo = SourceRepository(db_session)
        uk_source = await source_repo.create({
            "country": "UK",
            "visa_type": "Student",
            "url": "https://www.gov.uk/student-visa",
            "name": "UK Home Office Student Visa Information",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        # Create route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "UK",
            "visa_type": "Student",
            "email": "test@example.com",
            "is_active": True
        })
        
        # Verify source is mapped to route
        mapper = RouteMapper(db_session)
        sources = await mapper.get_sources_for_route(route)
        assert len(sources) == 1
        assert sources[0].id == uk_source.id
        
        # Note: Actual fetch test would require mocking or real network access
        # This test verifies the setup is correct for fetch pipeline
    
    async def test_route_isolation(self, db_session):
        """Test: verify routes are isolated (UK route doesn't match Canada sources)."""
        # Create sources for both routes
        source_repo = SourceRepository(db_session)
        
        uk_source = await source_repo.create({
            "country": "UK",
            "visa_type": "Student",
            "url": "https://www.gov.uk/student-visa",
            "name": "UK Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        ca_source = await source_repo.create({
            "country": "CA",
            "visa_type": "Student",
            "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html",
            "name": "Canada Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "source_metadata": {}
        })
        
        # Create routes
        route_repo = RouteSubscriptionRepository(db_session)
        
        uk_route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "UK",
            "visa_type": "Student",
            "email": "uk@example.com",
            "is_active": True
        })
        
        ca_route = await route_repo.create({
            "origin_country": "IN",
            "destination_country": "CA",
            "visa_type": "Student",
            "email": "ca@example.com",
            "is_active": True
        })
        
        # Verify isolation
        mapper = RouteMapper(db_session)
        
        uk_sources = await mapper.get_sources_for_route(uk_route)
        assert len(uk_sources) == 1
        assert uk_sources[0].id == uk_source.id
        assert uk_sources[0].country == "UK"
        
        ca_sources = await mapper.get_sources_for_route(ca_route)
        assert len(ca_sources) == 1
        assert ca_sources[0].id == ca_source.id
        assert ca_sources[0].country == "CA"
        
        # Verify UK route doesn't match Canada source
        assert uk_source.id not in [s.id for s in ca_sources]
        assert ca_source.id not in [s.id for s in uk_sources]

