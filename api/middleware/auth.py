"""Authentication middleware and dependencies."""

import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from api.database import get_db
from api.models.db.user import User
from api.repositories.user_repository import UserRepository
from api.auth.auth import decode_access_token

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency function to get the current authenticated user.
    
    Extracts JWT token from:
    1. Authorization header (Bearer token) - primary method
    2. Cookie (access_token) - fallback for web requests
    
    Args:
        request: FastAPI request object
        credentials: HTTPBearer credentials from Authorization header
        db: Database session
        
    Returns:
        User object for authenticated user
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found
    """
    token = None
    
    # Try to get token from Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Fallback: try to get token from cookie
        token = request.cookies.get("access_token")
    
    if not token:
        logger.warning(
            "Authentication attempt without token",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate token
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as e:
        logger.warning(
            f"Invalid or expired token: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(e).__name__,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Retrieve user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(username)
    
    if user is None:
        logger.warning(
            f"User not found for username: {username}",
            extra={
                "username": username,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(
            f"Inactive user attempted access: {username}",
            extra={
                "username": username,
                "user_id": str(user.id),
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

