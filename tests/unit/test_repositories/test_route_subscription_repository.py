"""Unit tests for RouteSubscriptionRepository."""

import pytest
import uuid
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.models.db.route_subscription import RouteSubscription


@pytest.mark.asyncio
class TestRouteSubscriptionRepository:
    """Tests for RouteSubscriptionRepository."""
    
    async def test_create_route_subscription(self, db_session, sample_route_subscription_data):
        """Test creating a route subscription."""
        repo = RouteSubscriptionRepository(db_session)
        route = await repo.create(sample_route_subscription_data)
        
        assert route.id is not None
        assert route.origin_country == "IN"
        assert route.destination_country == "DE"
        assert route.email == "test@example.com"
    
    async def test_get_by_id(self, db_session, sample_route_subscription_data):
        """Test getting route subscription by ID."""
        repo = RouteSubscriptionRepository(db_session)
        created = await repo.create(sample_route_subscription_data)
        
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_list_all(self, db_session, sample_route_subscription_data):
        """Test listing all route subscriptions."""
        repo = RouteSubscriptionRepository(db_session)
        
        route1 = await repo.create(sample_route_subscription_data)
        route2_data = sample_route_subscription_data.copy()
        route2_data["email"] = "test2@example.com"
        route2 = await repo.create(route2_data)
        
        all_routes = await repo.list_all()
        
        assert len(all_routes) >= 2
        assert any(r.id == route1.id for r in all_routes)
        assert any(r.id == route2.id for r in all_routes)
    
    async def test_list_active(self, db_session, sample_route_subscription_data):
        """Test listing active route subscriptions."""
        repo = RouteSubscriptionRepository(db_session)
        
        active_route = await repo.create(sample_route_subscription_data)
        inactive_data = sample_route_subscription_data.copy()
        inactive_data["is_active"] = False
        inactive_data["email"] = "inactive@example.com"
        inactive_route = await repo.create(inactive_data)
        
        active_routes = await repo.list_active()
        
        assert any(r.id == active_route.id for r in active_routes)
        assert not any(r.id == inactive_route.id for r in active_routes)
    
    async def test_get_by_route(self, db_session, sample_route_subscription_data):
        """Test getting route subscriptions by route."""
        repo = RouteSubscriptionRepository(db_session)
        
        route1 = await repo.create(sample_route_subscription_data)
        route2_data = sample_route_subscription_data.copy()
        route2_data["destination_country"] = "FR"
        route2 = await repo.create(route2_data)
        
        de_routes = await repo.get_by_route("IN", "DE", "Student")
        
        assert any(r.id == route1.id for r in de_routes)
        assert not any(r.id == route2.id for r in de_routes)
    
    async def test_update_route_subscription(self, db_session, sample_route_subscription_data):
        """Test updating a route subscription."""
        repo = RouteSubscriptionRepository(db_session)
        route = await repo.create(sample_route_subscription_data)
        
        updated = await repo.update(route.id, {"is_active": False})
        
        assert updated.is_active is False
        assert updated.id == route.id
    
    async def test_delete_route_subscription(self, db_session, sample_route_subscription_data):
        """Test deleting a route subscription."""
        repo = RouteSubscriptionRepository(db_session)
        route = await repo.create(sample_route_subscription_data)
        
        result = await repo.delete(route.id)
        
        assert result is True
        deleted = await repo.get_by_id(route.id)
        assert deleted is None
    
    async def test_exists(self, db_session, sample_route_subscription_data):
        """Test checking if route subscription exists."""
        repo = RouteSubscriptionRepository(db_session)
        await repo.create(sample_route_subscription_data)
        
        exists = await repo.exists("IN", "DE", "Student", "test@example.com")
        assert exists is True
        
        not_exists = await repo.exists("IN", "DE", "Student", "other@example.com")
        assert not_exists is False





