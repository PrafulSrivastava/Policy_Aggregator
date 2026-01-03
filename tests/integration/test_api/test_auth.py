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


class TestSignupEndpoint:
    """Tests for signup endpoint."""
    
    @pytest.mark.asyncio
    async def test_signup_with_valid_data(self, client, db_session):
        """Test signup with valid email and password."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "securepass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert "user" in data
        assert data["user"]["username"] == "newuser@example.com"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]
        assert "created_at" in data["user"]
    
    @pytest.mark.asyncio
    async def test_signup_with_duplicate_email(self, client, db_session):
        """Test signup with email that already exists."""
        # First create a user
        email = "existing@example.com"
        user_repo = UserRepository(db_session)
        user_data = {
            "username": email,
            "hashed_password": get_password_hash("password123"),
            "is_active": True
        }
        await user_repo.create(user_data)
        await db_session.commit()
        
        # Try to signup with same email
        response = client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": "anotherpassword123"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "Email already exists" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_signup_with_invalid_email_format(self, client, db_session):
        """Test signup with invalid email format."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "notanemail",
                "password": "securepass123"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_signup_with_short_password(self, client, db_session):
        """Test signup with password shorter than 8 characters."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "user@example.com",
                "password": "short"  # Less than 8 characters
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_signup_with_missing_fields(self, client, db_session):
        """Test signup with missing required fields."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "user@example.com"
                # Missing password
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_signup_creates_user_in_database(self, client, db_session):
        """Test that signup actually creates a user in the database."""
        email = "dbuser@example.com"
        password = "testpassword123"
        
        response = client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": password
            }
        )
        
        assert response.status_code == 201
        
        # Verify user exists in database
        user_repo = UserRepository(db_session)
        user = await user_repo.get_by_username(email)
        
        assert user is not None
        assert user.username == email
        assert user.is_active is True
        assert user.hashed_password is not None
        assert user.auth_provider == "password"
        
        # Verify password is hashed (not plain text)
        from api.auth.auth import verify_password
        assert verify_password(password, user.hashed_password)
        assert password != user.hashed_password  # Ensure it's hashed


class TestLogoutEndpoint:
    """Tests for logout endpoint."""
    
    def test_logout_endpoint(self, client):
        """Test logout endpoint."""
        response = client.post("/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Logged out successfully"

