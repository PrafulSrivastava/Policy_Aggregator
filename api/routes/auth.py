"""Authentication routes."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.schemas.user import LoginRequest, LoginResponse, UserResponse
from api.repositories.user_repository import UserRepository
from api.auth.auth import verify_password, create_access_token

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

