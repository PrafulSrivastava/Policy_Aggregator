"""Unit tests for OAuth service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.oauth_service import (
    generate_state_token,
    get_google_authorization_url,
    exchange_google_code,
    get_or_create_user_from_google
)


class TestOAuthService:
    """Tests for OAuth service functions."""
    
    def test_generate_state_token(self):
        """Test that state token generation returns a valid token."""
        state1 = generate_state_token()
        state2 = generate_state_token()
        
        # State tokens should be strings
        assert isinstance(state1, str)
        assert isinstance(state2, str)
        
        # State tokens should be different (random)
        assert state1 != state2
        
        # State tokens should be reasonably long (URL-safe base64)
        assert len(state1) > 20
    
    def test_get_google_authorization_url(self):
        """Test Google authorization URL generation."""
        with patch('api.services.oauth_service.settings') as mock_settings:
            mock_settings.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
            mock_settings.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
            
            state = "test-state-token"
            url = get_google_authorization_url(state)
            
            # URL should contain Google authorization endpoint
            assert "accounts.google.com/o/oauth2/v2/auth" in url
            
            # URL should contain required parameters
            assert "client_id=test-client-id" in url
            assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fgoogle%2Fcallback" in url
            assert "response_type=code" in url
            assert "state=test-state-token" in url
            assert "scope=openid+email+profile" in url
    
    def test_get_google_authorization_url_missing_config(self):
        """Test that missing OAuth config raises ValueError."""
        with patch('api.services.oauth_service.settings') as mock_settings:
            mock_settings.GOOGLE_OAUTH_CLIENT_ID = None
            mock_settings.GOOGLE_OAUTH_REDIRECT_URI = None
            
            with pytest.raises(ValueError, match="Google OAuth credentials not configured"):
                get_google_authorization_url("test-state")
    
    @pytest.mark.asyncio
    async def test_exchange_google_code_success(self):
        """Test successful code exchange."""
        with patch('api.services.oauth_service.settings') as mock_settings:
            mock_settings.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
            mock_settings.GOOGLE_OAUTH_CLIENT_SECRET = "test-client-secret"
            mock_settings.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
            
            # Mock HTTP responses
            mock_token_response = MagicMock()
            mock_token_response.json.return_value = {
                "access_token": "test-access-token",
                "token_type": "Bearer"
            }
            mock_token_response.raise_for_status = MagicMock()
            
            mock_userinfo_response = MagicMock()
            mock_userinfo_response.json.return_value = {
                "id": "google-user-123",
                "email": "user@example.com",
                "name": "Test User",
                "verified_email": True
            }
            mock_userinfo_response.raise_for_status = MagicMock()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                # Mock POST for token exchange
                mock_client_instance.post = AsyncMock(return_value=mock_token_response)
                # Mock GET for userinfo
                mock_client_instance.get = AsyncMock(return_value=mock_userinfo_response)
                
                user_info = await exchange_google_code("test-code", "test-state", "test-state")
                
                assert user_info["email"] == "user@example.com"
                assert user_info["id"] == "google-user-123"
                assert user_info["name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_exchange_google_code_state_mismatch(self):
        """Test that state mismatch raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state token"):
            await exchange_google_code("test-code", "wrong-state", "expected-state")
    
    @pytest.mark.asyncio
    async def test_exchange_google_code_missing_config(self):
        """Test that missing OAuth config raises ValueError."""
        with patch('api.services.oauth_service.settings') as mock_settings:
            mock_settings.GOOGLE_OAUTH_CLIENT_ID = None
            mock_settings.GOOGLE_OAUTH_CLIENT_SECRET = None
            mock_settings.GOOGLE_OAUTH_REDIRECT_URI = None
            
            with pytest.raises(ValueError, match="Google OAuth credentials not configured"):
                await exchange_google_code("test-code", "test-state", "test-state")
    
    @pytest.mark.asyncio
    async def test_exchange_google_code_http_error(self):
        """Test handling of HTTP errors during code exchange."""
        with patch('api.services.oauth_service.settings') as mock_settings:
            mock_settings.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
            mock_settings.GOOGLE_OAUTH_CLIENT_SECRET = "test-client-secret"
            mock_settings.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                # Mock HTTP error
                import httpx
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.text = "Invalid code"
                mock_error = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)
                mock_client_instance.post = AsyncMock(side_effect=mock_error)
                
                with pytest.raises(ValueError, match="Failed to exchange authorization code"):
                    await exchange_google_code("invalid-code", "test-state", "test-state")
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_google_new_user(self, db_session):
        """Test creating a new user from Google info."""
        from api.repositories.user_repository import UserRepository
        
        google_user_info = {
            "id": "google-user-123",
            "email": "newuser@example.com",
            "name": "New User",
            "verified_email": True
        }
        
        user = await get_or_create_user_from_google(google_user_info, db_session)
        
        assert user is not None
        assert user.username == "newuser@example.com"
        assert user.google_id == "google-user-123"
        assert user.auth_provider == "google"
        assert user.hashed_password is not None  # Random password generated
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_google_existing_user_by_email(self, db_session):
        """Test returning existing user found by email."""
        from api.repositories.user_repository import UserRepository
        from api.auth.auth import get_password_hash
        
        # Create existing user
        user_repo = UserRepository(db_session)
        existing_user = await user_repo.create({
            "username": "existing@example.com",
            "hashed_password": get_password_hash("password123"),
            "auth_provider": "password"
        })
        
        google_user_info = {
            "id": "google-user-456",
            "email": "existing@example.com",
            "name": "Existing User",
            "verified_email": True
        }
        
        user = await get_or_create_user_from_google(google_user_info, db_session)
        
        assert user.id == existing_user.id
        assert user.username == "existing@example.com"
        # Should update with Google ID
        assert user.google_id == "google-user-456"
        assert user.auth_provider == "google"
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_google_existing_user_by_google_id(self, db_session):
        """Test returning existing user found by Google ID."""
        from api.repositories.user_repository import UserRepository
        from api.auth.auth import get_password_hash
        
        # Create existing user with Google ID
        user_repo = UserRepository(db_session)
        existing_user = await user_repo.create({
            "username": "googleuser@example.com",
            "hashed_password": get_password_hash("password123"),
            "google_id": "google-user-789",
            "auth_provider": "google"
        })
        
        google_user_info = {
            "id": "google-user-789",
            "email": "googleuser@example.com",
            "name": "Google User",
            "verified_email": True
        }
        
        user = await get_or_create_user_from_google(google_user_info, db_session)
        
        assert user.id == existing_user.id
        assert user.google_id == "google-user-789"
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_google_missing_email(self, db_session):
        """Test that missing email raises ValueError."""
        google_user_info = {
            "id": "google-user-123",
            "name": "Test User",
            # Missing email
        }
        
        with pytest.raises(ValueError, match="Email not found in Google user info"):
            await get_or_create_user_from_google(google_user_info, db_session)



