"""Integration tests for OAuth endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from api.main import app
from api.database import get_db
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash


@pytest.fixture
async def client(db_session):
    """Create a test client for the FastAPI app with database dependency override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_google_oauth_config():
    """Mock Google OAuth configuration."""
    with patch('api.services.oauth_service.settings') as mock_settings:
        mock_settings.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
        mock_settings.GOOGLE_OAUTH_CLIENT_SECRET = "test-client-secret"
        mock_settings.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
        yield mock_settings


class TestGoogleOAuthStart:
    """Tests for GET /auth/google endpoint."""
    
    def test_google_oauth_start_redirects(self, client, mock_google_oauth_config):
        """Test that /auth/google redirects to Google authorization URL."""
        response = client.get("/auth/google", follow_redirects=False)
        
        assert response.status_code == 302
        assert "accounts.google.com/o/oauth2/v2/auth" in response.headers["location"]
        assert "client_id=test-client-id" in response.headers["location"]
        assert "state=" in response.headers["location"]
        
        # Check that state cookie is set
        assert "oauth_state" in response.cookies
    
    def test_google_oauth_start_not_configured(self, client):
        """Test that /auth/google returns 501 if not configured."""
        with patch('api.routes.auth.settings') as mock_settings:
            mock_settings.GOOGLE_OAUTH_CLIENT_ID = None
            mock_settings.GOOGLE_OAUTH_REDIRECT_URI = None
            
            response = client.get("/auth/google")
            
            assert response.status_code == 501
            data = response.json()
            assert "not configured" in data["detail"].lower()


class TestGoogleOAuthCallback:
    """Tests for GET /auth/google/callback endpoint."""
    
    @pytest.mark.asyncio
    async def test_oauth_callback_success(self, client, db_session, mock_google_oauth_config):
        """Test successful OAuth callback creates/authenticates user."""
        # Mock Google OAuth code exchange
        mock_user_info = {
            "id": "google-user-123",
            "email": "oauthuser@example.com",
            "name": "OAuth User",
            "verified_email": True
        }
        
        with patch('api.services.oauth_service.exchange_google_code') as mock_exchange:
            mock_exchange.return_value = mock_user_info
            
            # Get state token from initial redirect
            start_response = client.get("/auth/google", follow_redirects=False)
            state_cookie = start_response.cookies.get("oauth_state")
            
            # Mock state verification (we'll use the actual signed cookie)
            with patch('api.routes.auth.verify_signed_state_cookie') as mock_verify:
                # Extract state from the redirect URL
                redirect_url = start_response.headers["location"]
                import urllib.parse
                parsed = urllib.parse.urlparse(redirect_url)
                params = urllib.parse.parse_qs(parsed.query)
                actual_state = params.get("state", [""])[0]
                
                mock_verify.return_value = actual_state
                
                # Call callback with authorization code
                response = client.get(
                    f"/auth/google/callback?code=test-auth-code&state={actual_state}",
                    cookies={"oauth_state": state_cookie},
                    follow_redirects=False
                )
                
                # Should redirect to dashboard
                assert response.status_code == 302
                assert response.headers["location"] == "/"
                
                # Check that access token cookie is set
                assert "access_token" in response.cookies
    
    def test_oauth_callback_user_denied(self, client, mock_google_oauth_config):
        """Test OAuth callback when user denies access."""
        response = client.get(
            "/auth/google/callback?error=access_denied",
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert "/login?error=oauth_denied" in response.headers["location"]
    
    def test_oauth_callback_missing_code(self, client, mock_google_oauth_config):
        """Test OAuth callback with missing code parameter."""
        response = client.get(
            "/auth/google/callback?state=test-state",
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert "/login?error=oauth_invalid" in response.headers["location"]
    
    def test_oauth_callback_invalid_state(self, client, mock_google_oauth_config):
        """Test OAuth callback with invalid state token."""
        with patch('api.routes.auth.verify_signed_state_cookie') as mock_verify:
            mock_verify.side_effect = ValueError("Invalid state token")
            
            response = client.get(
                "/auth/google/callback?code=test-code&state=invalid-state",
                cookies={"oauth_state": "invalid-cookie"},
                follow_redirects=False
            )
            
            assert response.status_code == 302
            assert "/login?error=oauth_invalid" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_oauth_callback_exchange_error(self, client, db_session, mock_google_oauth_config):
        """Test OAuth callback when code exchange fails."""
        with patch('api.services.oauth_service.exchange_google_code') as mock_exchange:
            mock_exchange.side_effect = ValueError("Failed to exchange code")
            
            # Get state token from initial redirect
            start_response = client.get("/auth/google", follow_redirects=False)
            state_cookie = start_response.cookies.get("oauth_state")
            
            redirect_url = start_response.headers["location"]
            import urllib.parse
            parsed = urllib.parse.urlparse(redirect_url)
            params = urllib.parse.parse_qs(parsed.query)
            actual_state = params.get("state", [""])[0]
            
            with patch('api.routes.auth.verify_signed_state_cookie') as mock_verify:
                mock_verify.return_value = actual_state
                
                response = client.get(
                    f"/auth/google/callback?code=invalid-code&state={actual_state}",
                    cookies={"oauth_state": state_cookie},
                    follow_redirects=False
                )
                
                assert response.status_code == 302
                assert "/login?error=oauth_failed" in response.headers["location"]


class TestOAuthJWTToken:
    """Tests for JWT token generation after OAuth login."""
    
    @pytest.mark.asyncio
    async def test_oauth_jwt_token_format(self, client, db_session, mock_google_oauth_config):
        """Test that OAuth-generated JWT tokens have same format as password auth."""
        from api.auth.auth import decode_access_token
        
        mock_user_info = {
            "id": "google-user-123",
            "email": "jwtuser@example.com",
            "name": "JWT User",
            "verified_email": True
        }
        
        with patch('api.services.oauth_service.exchange_google_code') as mock_exchange:
            mock_exchange.return_value = mock_user_info
            
            # Get state token
            start_response = client.get("/auth/google", follow_redirects=False)
            state_cookie = start_response.cookies.get("oauth_state")
            
            redirect_url = start_response.headers["location"]
            import urllib.parse
            parsed = urllib.parse.urlparse(redirect_url)
            params = urllib.parse.parse_qs(parsed.query)
            actual_state = params.get("state", [""])[0]
            
            with patch('api.routes.auth.verify_signed_state_cookie') as mock_verify:
                mock_verify.return_value = actual_state
                
                # Complete OAuth flow
                callback_response = client.get(
                    f"/auth/google/callback?code=test-code&state={actual_state}",
                    cookies={"oauth_state": state_cookie},
                    follow_redirects=False
                )
                
                # Extract JWT token from cookie
                access_token = callback_response.cookies.get("access_token")
                assert access_token is not None
                
                # Decode token and verify format
                payload = decode_access_token(access_token)
                assert "sub" in payload
                assert "exp" in payload
                assert payload["sub"] == "jwtuser@example.com"


class TestOAuthProtectedRoutes:
    """Tests that OAuth-generated tokens work with protected routes."""
    
    @pytest.mark.asyncio
    async def test_oauth_token_protected_route(self, client, db_session, mock_google_oauth_config):
        """Test that OAuth-generated token works with protected routes."""
        mock_user_info = {
            "id": "google-user-123",
            "email": "protected@example.com",
            "name": "Protected User",
            "verified_email": True
        }
        
        with patch('api.services.oauth_service.exchange_google_code') as mock_exchange:
            mock_exchange.return_value = mock_user_info
            
            # Complete OAuth flow
            start_response = client.get("/auth/google", follow_redirects=False)
            state_cookie = start_response.cookies.get("oauth_state")
            
            redirect_url = start_response.headers["location"]
            import urllib.parse
            parsed = urllib.parse.urlparse(redirect_url)
            params = urllib.parse.parse_qs(parsed.query)
            actual_state = params.get("state", [""])[0]
            
            with patch('api.routes.auth.verify_signed_state_cookie') as mock_verify:
                mock_verify.return_value = actual_state
                
                callback_response = client.get(
                    f"/auth/google/callback?code=test-code&state={actual_state}",
                    cookies={"oauth_state": state_cookie},
                    follow_redirects=False
                )
                
                access_token = callback_response.cookies.get("access_token")
                
                # Use token to access protected route
                response = client.get(
                    "/api/dashboard",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                assert response.status_code == 200

