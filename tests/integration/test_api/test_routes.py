"""Integration tests for route subscription API endpoints."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from api.main import app
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash, create_access_token


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def test_user(db_session):
    """Create a test user in the database."""
    user_repo = UserRepository(db_session)
    user_data = {
        "username": "testuser",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True
    }
    user = await user_repo.create(user_data)
    await db_session.commit()
    return user


@pytest.fixture
async def sample_route(db_session):
    """Create a sample route subscription in the database."""
    route_repo = RouteSubscriptionRepository(db_session)
    route_data = {
        "origin_country": "IN",
        "destination_country": "DE",
        "visa_type": "Student",
        "email": "test@example.com",
        "is_active": True
    }
    route = await route_repo.create(route_data)
    await db_session.commit()
    return route


class TestListRoutes:
    """Tests for GET /api/routes endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_routes_with_authentication(self, client, test_user, sample_route):
        """Test listing routes with valid authentication."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/routes",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_list_routes_without_authentication(self, client):
        """Test listing routes without authentication returns 401."""
        response = client.get("/api/routes")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_routes_pagination(self, client, test_user, db_session):
        """Test pagination parameters."""
        # Create multiple routes
        route_repo = RouteSubscriptionRepository(db_session)
        for i in range(5):
            route_data = {
                "origin_country": "IN",
                "destination_country": "DE",
                "visa_type": f"Student{i}",
                "email": f"test{i}@example.com",
                "is_active": True
            }
            await route_repo.create(route_data)
        await db_session.commit()
        
        # Test first page
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/routes?page=1&page_size=2",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestCreateRoute:
    """Tests for POST /api/routes endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_route_with_valid_data(self, client, test_user):
        """Test creating a route with valid data."""
        auth_token = create_access_token(data={"sub": test_user.username})
        route_data = {
            "origin_country": "IN",
            "destination_country": "DE",
            "visa_type": "Work",
            "email": "newuser@example.com",
            "is_active": True
        }
        
        response = client.post(
            "/api/routes",
            json=route_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["origin_country"] == "IN"
        assert data["destination_country"] == "DE"
        assert data["visa_type"] == "Work"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_route_without_authentication(self, client):
        """Test creating a route without authentication returns 401."""
        route_data = {
            "origin_country": "IN",
            "destination_country": "DE",
            "visa_type": "Student",
            "email": "test@example.com"
        }
        
        response = client.post("/api/routes", json=route_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_route_with_invalid_data(self, client, test_user):
        """Test creating a route with invalid data returns 400."""
        auth_token = create_access_token(data={"sub": test_user.username})
        # Missing required field
        route_data = {
            "origin_country": "IN",
            "destination_country": "DE"
            # Missing visa_type and email
        }
        
        response = client.post(
            "/api/routes",
            json=route_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_route_with_invalid_email(self, client, test_user):
        """Test creating a route with invalid email returns 400."""
        auth_token = create_access_token(data={"sub": test_user.username})
        route_data = {
            "origin_country": "IN",
            "destination_country": "DE",
            "visa_type": "Student",
            "email": "invalid-email"  # Invalid email format
        }
        
        response = client.post(
            "/api/routes",
            json=route_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_route_duplicate(self, client, test_user, sample_route):
        """Test creating a duplicate route returns 409."""
        auth_token = create_access_token(data={"sub": test_user.username})
        route_data = {
            "origin_country": "IN",
            "destination_country": "DE",
            "visa_type": "Student",
            "email": "test@example.com"  # Same as sample_route
        }
        
        response = client.post(
            "/api/routes",
            json=route_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "DUPLICATE_ROUTE" in str(data["detail"])


class TestGetRoute:
    """Tests for GET /api/routes/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_route_with_valid_id(self, client, test_user, sample_route):
        """Test getting a route with valid ID."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            f"/api/routes/{sample_route.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(sample_route.id)
        assert data["origin_country"] == "IN"
        assert data["destination_country"] == "DE"
        assert data["visa_type"] == "Student"
    
    def test_get_route_without_authentication(self, client, sample_route):
        """Test getting a route without authentication returns 401."""
        response = client.get(f"/api/routes/{sample_route.id}")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_route_with_invalid_id(self, client, test_user):
        """Test getting a route with invalid ID returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        invalid_id = uuid4()
        
        response = client.get(
            f"/api/routes/{invalid_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "ROUTE_NOT_FOUND" in str(data["detail"])


class TestDeleteRoute:
    """Tests for DELETE /api/routes/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_route_with_valid_id(self, client, test_user, db_session):
        """Test deleting a route with valid ID."""
        auth_token = create_access_token(data={"sub": test_user.username})
        # Create a route to delete
        route_repo = RouteSubscriptionRepository(db_session)
        route_data = {
            "origin_country": "IN",
            "destination_country": "FR",
            "visa_type": "Work",
            "email": "delete@example.com",
            "is_active": True
        }
        route = await route_repo.create(route_data)
        await db_session.commit()
        
        response = client.delete(
            f"/api/routes/{route.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify route is deleted
        deleted_route = await route_repo.get_by_id(route.id)
        assert deleted_route is None
    
    def test_delete_route_without_authentication(self, client, sample_route):
        """Test deleting a route without authentication returns 401."""
        response = client.delete(f"/api/routes/{sample_route.id}")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_delete_route_with_invalid_id(self, client, test_user):
        """Test deleting a route with invalid ID returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        invalid_id = uuid4()
        
        response = client.delete(
            f"/api/routes/{invalid_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "ROUTE_NOT_FOUND" in str(data["detail"])

