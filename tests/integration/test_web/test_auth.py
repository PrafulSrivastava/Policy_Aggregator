"""Integration tests for web authentication routes."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database import get_db
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash, create_access_token


@pytest.fixture
async def client(db_session):
    """Create a test client for the FastAPI app with database dependency override."""
    # Override get_db dependency to use test database session
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, follow_redirects=False)
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


class TestLoginPage:
    """Tests for GET /login endpoint."""
    
    def test_login_page_renders(self, client):
        """Test that GET /login renders the login page."""
        response = client.get("/login")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Username" in response.text
        assert "Password" in response.text
        assert "Sign in" in response.text
    
    @pytest.mark.asyncio
    async def test_login_page_redirects_when_authenticated(self, client, test_user):
        """Test that GET /login redirects to dashboard if already authenticated."""
        # Create a token and set it as a cookie
        token = create_access_token(data={"sub": test_user.username})
        
        response = client.get("/login", cookies={"access_token": token})
        
        # Should redirect to dashboard
        assert response.status_code == 302
        assert response.headers["location"] == "/"


class TestLoginPost:
    """Tests for POST /login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials_redirects(self, client, test_user):
        """Test that POST /login with valid credentials redirects to dashboard."""
        response = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["location"] == "/"
        
        # Check that cookie is set
        assert "access_token" in response.cookies
        assert response.cookies["access_token"] is not None
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_username_shows_error(self, client):
        """Test that POST /login with invalid username shows error message."""
        response = client.post(
            "/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        assert "text/html" in response.headers["content-type"]
        assert "Incorrect username or password" in response.text
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_password_shows_error(self, client, test_user):
        """Test that POST /login with invalid password shows error message."""
        response = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "text/html" in response.headers["content-type"]
        assert "Incorrect username or password" in response.text


class TestProtectedRoutes:
    """Tests for protected web routes."""
    
    def test_protected_route_without_auth_redirects(self, client):
        """Test that accessing protected route without auth redirects to login."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    def test_protected_route_with_invalid_token_redirects(self, client):
        """Test that accessing protected route with invalid token redirects to login."""
        response = client.get(
            "/",
            cookies={"access_token": "invalid.token.here"},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_protected_route_with_auth_shows_page(self, client, test_user):
        """Test that accessing protected route with valid auth shows the page."""
        token = create_access_token(data={"sub": test_user.username})
        
        response = client.get("/", cookies={"access_token": token})
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Dashboard" in response.text
    
    @pytest.mark.asyncio
    async def test_routes_page_with_auth(self, client, test_user):
        """Test that /routes page is accessible with valid auth."""
        token = create_access_token(data={"sub": test_user.username})
        
        response = client.get("/routes", cookies={"access_token": token})
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Route Subscriptions" in response.text
    
    @pytest.mark.asyncio
    async def test_sources_page_with_auth(self, client, test_user):
        """Test that /sources page is accessible with valid auth."""
        token = create_access_token(data={"sub": test_user.username})
        
        response = client.get("/sources", cookies={"access_token": token})
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Sources" in response.text
    
    @pytest.mark.asyncio
    async def test_changes_page_with_auth(self, client, test_user):
        """Test that /changes page is accessible with valid auth."""
        token = create_access_token(data={"sub": test_user.username})
        
        response = client.get("/changes", cookies={"access_token": token})
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Policy Changes" in response.text
    
    @pytest.mark.asyncio
    async def test_trigger_page_with_auth(self, client, test_user):
        """Test that /trigger page is accessible with valid auth."""
        token = create_access_token(data={"sub": test_user.username})
        
        response = client.get("/trigger", cookies={"access_token": token})
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Manual Trigger" in response.text


class TestLogout:
    """Tests for POST /logout endpoint."""
    
    @pytest.mark.asyncio
    async def test_logout_clears_session_and_redirects(self, client, test_user):
        """Test that POST /logout clears session cookie and redirects to login."""
        token = create_access_token(data={"sub": test_user.username})
        
        # First, login to set the cookie
        login_response = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            },
            follow_redirects=False
        )
        
        # Verify cookie is set
        assert "access_token" in login_response.cookies
        
        # Now logout
        response = client.post("/logout", follow_redirects=False)
        
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
        
        # Check that cookie is deleted (max_age=0 or cookie not present)
        # TestClient may not show deleted cookies, so verify by trying to access protected route
        protected_response = client.get("/", cookies=response.cookies, follow_redirects=False)
        assert protected_response.status_code == 302
        assert protected_response.headers["location"] == "/login"

