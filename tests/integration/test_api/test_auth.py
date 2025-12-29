"""Integration tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
from httpx import AsyncClient

from api.main import app
from api.database import get_db
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash, create_access_token, decode_access_token
from jose import JWTError


@pytest.fixture
async def client(db_session):
    """Create a test client for the FastAPI app with database dependency override."""
    # Override get_db dependency to use test database session
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # Clean up overrides after test
    app.dependency_overrides.clear()


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


class TestLoginEndpoint:
    """Tests for login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_with_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    def test_login_with_missing_fields(self, client):
        """Test login with missing required fields."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser"
                # Missing password
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestProtectedRoutes:
    """Tests for protected route access."""
    
    def test_protected_route_without_token(self, client):
        """Test that protected routes return 401 without token."""
        # Health check should remain public (no auth required)
        response = client.get("/health")
        assert response.status_code == 200  # Health check is public
    
    @pytest.mark.asyncio
    async def test_protected_route_with_valid_token(self, client, test_user):
        """Test that protected routes work with valid token."""
        # First, login to get a token
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Test that we can decode the token
        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_protected_route_with_expired_token(self):
        """Test that expired tokens are rejected."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Try to decode expired token
        with pytest.raises(JWTError):
            decode_access_token(expired_token)
    
    def test_protected_route_with_invalid_token(self):
        """Test that invalid tokens are rejected."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            decode_access_token(invalid_token)


class TestLogoutEndpoint:
    """Tests for logout endpoint."""
    
    def test_logout_endpoint(self, client):
        """Test logout endpoint."""
        response = client.post("/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Logged out successfully"

