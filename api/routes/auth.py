"""Authentication routes."""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from api.database import get_db
from api.models.schemas.user import LoginRequest, LoginResponse, SignupRequest, SignupResponse, UserResponse
from api.repositories.user_repository import UserRepository
from api.auth.auth import verify_password, create_access_token, get_password_hash
from api.services.oauth_service import (
    generate_state_token,
    get_google_authorization_url,
    exchange_google_code,
    get_or_create_user_from_google
)
from api.config import settings, Environment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    login_request: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Login endpoint that validates credentials and returns JWT token.
    
    Args:
        login_request: Login credentials (username and password)
        response: FastAPI response object for setting cookies
        db: Database session
        
    Returns:
        LoginResponse with access_token and token_type
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(login_request.username)
    
    # Validate user exists and is active
    if not user or not user.is_active:
        logger.warning(
            f"Failed login attempt - invalid username or inactive account: {login_request.username}",
            extra={
                "username": login_request.username,
                "reason": "user_not_found_or_inactive",
                "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if user has password (OAuth-only users don't have passwords)
    if not user.hashed_password:
        logger.warning(
            f"Login attempt with password for OAuth-only user: {login_request.username}",
            extra={
                "username": login_request.username,
                "reason": "oauth_only_user",
                "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google OAuth. Please sign in with Google."
        )
    
    # Verify password
    if not verify_password(login_request.password, user.hashed_password):
        logger.warning(
            f"Failed login attempt - incorrect password: {login_request.username}",
            extra={
                "username": login_request.username,
                "reason": "invalid_password",
                "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Update last login timestamp
    await user_repo.update(user.id, {"last_login_at": datetime.utcnow()})
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})
    
    # Set session cookie (optional, for web requests)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400  # 24 hours in seconds
    )
    
    logger.info(
        f"User logged in successfully: {login_request.username}",
        extra={
            "username": login_request.username,
            "user_id": str(user.id),
            "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_request: SignupRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> SignupResponse:
    """
    Signup endpoint that creates a new user account and returns JWT token.
    
    Args:
        signup_request: Signup credentials (email and password)
        request: FastAPI request object
        response: FastAPI response object for setting cookies
        db: Database session
        
    Returns:
        SignupResponse with access_token, token_type, and user info
        
    Raises:
        HTTPException: 409 if email already exists, 400 for validation errors
    """
    user_repo = UserRepository(db)
    
    # Check if email already exists (email is used as username)
    existing_user = await user_repo.get_by_username(signup_request.email)
    if existing_user:
        logger.warning(
            f"Signup attempt with existing email: {signup_request.email}",
            extra={
                "email": signup_request.email,
                "reason": "email_already_exists",
                "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    
    # Hash password
    hashed_password = get_password_hash(signup_request.password)
    
    # Create user
    user_data = {
        "username": signup_request.email,  # Email is used as username
        "hashed_password": hashed_password,
        "is_active": True,
        "auth_provider": "password"
    }
    
    try:
        user = await user_repo.create(user_data)
    except Exception as e:
        logger.error(
            f"Error creating user during signup: {str(e)}",
            extra={
                "email": signup_request.email,
                "error": str(e),
                "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})
    
    # Set session cookie (optional, for web requests)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400  # 24 hours in seconds
    )
    
    logger.info(
        f"User signed up successfully: {signup_request.email}",
        extra={
            "username": signup_request.email,
            "user_id": str(user.id),
            "client_ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
        }
    )
    
    return SignupResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict:
    """
    Logout endpoint (optional for token-based auth).
    
    For JWT tokens, logout is handled client-side by removing the token.
    This endpoint clears the session cookie if it exists.
    
    Args:
        response: FastAPI response object for clearing cookies
        
    Returns:
        Success message
    """
    # Clear the access token cookie
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    
    return {"message": "Logged out successfully"}


def create_signed_state_cookie(state: str) -> str:
    """
    Create a signed state cookie value using JWT.
    
    Args:
        state: State token to sign
        
    Returns:
        Signed JWT token containing state
    """
    return jwt.encode(
        {"state": state, "type": "oauth_state"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_signed_state_cookie(signed_state: str) -> str:
    """
    Verify and extract state from signed cookie.
    
    Args:
        signed_state: Signed JWT token containing state
        
    Returns:
        Extracted state token
        
    Raises:
        ValueError: If signed state is invalid
    """
    try:
        payload = jwt.decode(
            signed_state,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "oauth_state":
            raise ValueError("Invalid state token type")
        return payload.get("state")
    except Exception as e:
        raise ValueError(f"Invalid state token: {str(e)}")


@router.get("/google")
async def google_oauth_start(request: Request) -> RedirectResponse:
    """
    Start Google OAuth flow.
    
    Generates a state token and redirects to Google authorization URL.
    
    Args:
        request: FastAPI request object
        
    Returns:
        RedirectResponse to Google OAuth authorization URL
        
    Raises:
        HTTPException: If Google OAuth is not configured
    """
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_REDIRECT_URI:
        logger.error("Google OAuth not configured")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    # Generate state token
    state = generate_state_token()
    
    # Create signed state cookie
    signed_state = create_signed_state_cookie(state)
    
    # Generate Google authorization URL
    auth_url = get_google_authorization_url(state)
    
    # Create response with redirect
    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    
    # Set state in signed cookie (HttpOnly, Secure, SameSite=Strict)
    response.set_cookie(
        key="oauth_state",
        value=signed_state,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",  # Use 'lax' to allow redirect from Google
        max_age=600  # 10 minutes
    )
    
    logger.info("Google OAuth flow started")
    
    return response


@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    response: Response,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for user info, creates/authenticates user,
    and redirects to dashboard with JWT token in cookie.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        code: Authorization code from Google
        state: State token from Google
        error: Error parameter if user denied access
        db: Database session
        
    Returns:
        RedirectResponse to dashboard on success, login page on error
    """
    # Get frontend URL for redirects
    frontend_url = settings.FRONTEND_URL
    
    # Handle user denial
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(
            url=f"{frontend_url}/#/login?error=oauth_denied",
            status_code=status.HTTP_302_FOUND
        )
    
    # Validate required parameters
    if not code or not state:
        logger.warning("Missing code or state in OAuth callback")
        return RedirectResponse(
            url=f"{frontend_url}/#/login?error=oauth_invalid",
            status_code=status.HTTP_302_FOUND
        )
    
    # Get and verify state from cookie
    oauth_state_cookie = request.cookies.get("oauth_state")
    if not oauth_state_cookie:
        logger.warning("OAuth state cookie not found")
        return RedirectResponse(
            url=f"{frontend_url}/#/login?error=oauth_invalid",
            status_code=status.HTTP_302_FOUND
        )
    
    try:
        expected_state = verify_signed_state_cookie(oauth_state_cookie)
    except ValueError as e:
        logger.warning(f"Invalid OAuth state token: {str(e)}")
        return RedirectResponse(
            url=f"{frontend_url}/#/login?error=oauth_invalid",
            status_code=status.HTTP_302_FOUND
        )
    
    # Clear OAuth state cookie
    response.delete_cookie(key="oauth_state", httponly=True, samesite="lax")
    
    try:
        # Exchange code for user info
        google_user_info = await exchange_google_code(code, state, expected_state)
        
        # Get or create user
        user = await get_or_create_user_from_google(google_user_info, db)
        
        # Update last login
        user_repo = UserRepository(db)
        await user_repo.update(user.id, {"last_login_at": datetime.utcnow()})
        
        # Create JWT token (same format as password auth)
        access_token = create_access_token(data={"sub": user.username})
        
        # Set JWT token in cookie (for same-origin requests)
        # Use secure=False in development, secure=True in production
        is_secure = settings.ENVIRONMENT == Environment.PRODUCTION
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_secure,  # True in production with HTTPS, False in development
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        logger.info(
            f"User logged in successfully via Google OAuth: {user.username}",
            extra={
                "username": user.username,
                "user_id": str(user.id),
                "auth_provider": "google"
            }
        )
        
        # Redirect to dashboard with token in URL (for cross-origin cookie issue)
        # Frontend will extract token from URL and store in localStorage
        # URL-encode the token to handle special characters
        redirect_url = f"{frontend_url}/#/?token={quote(access_token)}"
        
        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND
        )
        
    except ValueError as e:
        logger.error(f"OAuth error: {str(e)}")
        return RedirectResponse(
            url=f"{frontend_url}/#/login?error=oauth_failed",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"Unexpected OAuth error: {str(e)}", exc_info=True)
        return RedirectResponse(
            url=f"{frontend_url}/#/login?error=oauth_failed",
            status_code=status.HTTP_302_FOUND
        )

