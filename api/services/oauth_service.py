"""OAuth service for Google OAuth 2.0 authentication."""

import logging
import secrets
from typing import Optional, Dict, Any, TYPE_CHECKING
from urllib.parse import urlencode
import httpx

from api.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth scopes
GOOGLE_OAUTH_SCOPES = ["openid", "email", "profile"]


def generate_state_token() -> str:
    """
    Generate a random state token for CSRF protection.
    
    Returns:
        Random state token string
    """
    return secrets.token_urlsafe(32)


def get_google_authorization_url(state: str) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Args:
        state: State token for CSRF protection
        
    Returns:
        Google OAuth authorization URL
        
    Raises:
        ValueError: If Google OAuth credentials are not configured
    """
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_REDIRECT_URI:
        raise ValueError("Google OAuth credentials not configured")
    
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_OAUTH_SCOPES),
        "state": state,
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Force consent screen to get refresh token
    }
    
    return f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(params)}"


async def exchange_google_code(code: str, state: str, expected_state: str) -> Dict[str, Any]:
    """
    Exchange Google authorization code for user info.
    
    Args:
        code: Authorization code from Google
        state: State token from callback
        expected_state: Expected state token (for CSRF protection)
        
    Returns:
        Dictionary with user info (email, name, etc.)
        
    Raises:
        ValueError: If state doesn't match or credentials not configured
        HTTPException: If code exchange fails
    """
    # Verify state token (CSRF protection)
    if state != expected_state:
        logger.warning("OAuth state token mismatch - possible CSRF attack")
        raise ValueError("Invalid state token")
    
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET or not settings.GOOGLE_OAUTH_REDIRECT_URI:
        raise ValueError("Google OAuth credentials not configured")
    
    # Exchange authorization code for access token
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token in response")
            
            # Fetch user info from Google
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
            
            logger.info(
                f"Successfully exchanged Google OAuth code for user info",
                extra={"email": user_info.get("email")}
            )
            
            return user_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to exchange Google OAuth code: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to exchange authorization code: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Network error during Google OAuth code exchange: {str(e)}")
            raise ValueError(f"Network error during OAuth: {str(e)}")


async def get_or_create_user_from_google(
    google_user_info: Dict[str, Any],
    db_session: "AsyncSession"
) -> Any:
    """
    Get or create user from Google user info.
    
    Args:
        google_user_info: Dictionary with Google user info (email, name, etc.)
        db_session: Database session
        
    Returns:
        User instance
        
    Raises:
        ValueError: If email is missing from Google user info
    """
    from api.repositories.user_repository import UserRepository
    from api.auth.auth import get_password_hash
    
    email = google_user_info.get("email")
    if not email:
        raise ValueError("Email not found in Google user info")
    
    google_id = google_user_info.get("id")
    name = google_user_info.get("name", email.split("@")[0])
    
    user_repo = UserRepository(db_session)
    
    # First check if user exists by Google ID
    user = None
    if google_id:
        user = await user_repo.get_by_google_id(google_id)
    
    # If not found by Google ID, check by email (using email as username)
    if not user:
        user = await user_repo.get_by_username(email)
    
    if user:
        # Update user with Google ID and auth provider if not set
        update_data = {}
        if google_id and not user.google_id:
            update_data["google_id"] = google_id
        if user.auth_provider != "google":
            update_data["auth_provider"] = "google"
        
        if update_data:
            await user_repo.update(user.id, update_data)
            await db_session.refresh(user)
        
        logger.info(f"Existing user logged in via Google OAuth: {email}")
        return user
    
    # Create new user
    # For OAuth users, we generate a random password (they won't use it)
    # In production, you might want to make password nullable for OAuth-only users
    random_password = secrets.token_urlsafe(32)
    
    user_data = {
        "username": email,
        "hashed_password": get_password_hash(random_password),  # Random password for OAuth users
        "google_id": google_id,
        "auth_provider": "google",
        "is_active": True,
    }
    
    user = await user_repo.create(user_data)
    logger.info(f"Created new user via Google OAuth: {email}")
    
    return user

