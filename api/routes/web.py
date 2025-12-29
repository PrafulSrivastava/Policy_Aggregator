"""Web routes for admin UI."""

import logging
from fastapi import APIRouter, Depends, Request, Response, status, Form, HTTPException, Query
from typing import Optional
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.repositories.user_repository import UserRepository
from api.auth.auth import verify_password, create_access_token
from api.middleware.auth import get_current_user, get_current_user_web, WebAuthRedirectException
from api.models.db.user import User
from api.templates import templates

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: Optional[str] = Query(None)
):
    """
    Render login page.
    
    If user is already authenticated, redirect to dashboard.
    
    Args:
        request: FastAPI request object
        error: Optional error message from query parameter (e.g., from OAuth callback)
        
    Returns:
        HTMLResponse with login page or redirect to dashboard
    """
    # Check if user is already authenticated via cookie
    # Only check token format, don't verify user exists (to avoid DB dependency)
    token = request.cookies.get("access_token")
    if token:
        try:
            from api.auth.auth import decode_access_token
            
            # Try to decode token - if valid format, redirect to dashboard
            # Full user verification will happen when accessing protected routes
            payload = decode_access_token(token)
            if payload.get("sub"):
                return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        except Exception:
            # Token invalid, show login page
            pass
    
    # Map OAuth error codes to user-friendly messages
    error_message = None
    if error:
        error_messages = {
            "oauth_denied": "Google OAuth access was denied. Please try again.",
            "oauth_invalid": "Invalid OAuth request. Please try again.",
            "oauth_failed": "Google OAuth authentication failed. Please try again or use password login.",
        }
        error_message = error_messages.get(error, "An error occurred. Please try again.")
    
    # Check if Google OAuth is configured
    from api.config import settings
    google_oauth_enabled = bool(
        settings.GOOGLE_OAUTH_CLIENT_ID and 
        settings.GOOGLE_OAUTH_CLIENT_SECRET and 
        settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    
    return templates.TemplateResponse(
        "pages/login.html",
        {
            "request": request, 
            "user": None, 
            "error": error_message,
            "google_oauth_enabled": google_oauth_enabled
        }
    )


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle login form submission.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object for setting cookies
        username: Username from form
        password: Password from form
        db: Database session
        
    Returns:
        RedirectResponse to dashboard on success, or login page with error on failure
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(username)
    
    # Validate user exists and is active
    if not user or not user.is_active:
        logger.warning(
            f"Failed login attempt - invalid username or inactive account: {username}",
            extra={
                "username": username,
                "reason": "user_not_found_or_inactive",
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        return templates.TemplateResponse(
            "pages/login.html",
            {
                "request": request,
                "user": None,
                "error": "Incorrect username or password"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user has password (OAuth-only users don't have passwords)
    if not user.hashed_password:
        logger.warning(
            f"Login attempt with password for OAuth-only user: {username}",
            extra={
                "username": username,
                "reason": "oauth_only_user",
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        from api.config import settings
        google_oauth_enabled = bool(
            settings.GOOGLE_OAUTH_CLIENT_ID and 
            settings.GOOGLE_OAUTH_CLIENT_SECRET and 
            settings.GOOGLE_OAUTH_REDIRECT_URI
        )
        return templates.TemplateResponse(
            "pages/login.html",
            {
                "request": request,
                "user": None,
                "error": "This account uses Google OAuth. Please sign in with Google.",
                "google_oauth_enabled": google_oauth_enabled
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        logger.warning(
            f"Failed login attempt - incorrect password: {username}",
            extra={
                "username": username,
                "reason": "invalid_password",
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        from api.config import settings
        google_oauth_enabled = bool(
            settings.GOOGLE_OAUTH_CLIENT_ID and 
            settings.GOOGLE_OAUTH_CLIENT_SECRET and 
            settings.GOOGLE_OAUTH_REDIRECT_URI
        )
        return templates.TemplateResponse(
            "pages/login.html",
            {
                "request": request,
                "user": None,
                "error": "Incorrect username or password",
                "google_oauth_enabled": google_oauth_enabled
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})
    
    # Set session cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400  # 24 hours in seconds
    )
    
    logger.info(
        f"User logged in successfully: {username}",
        extra={
            "username": username,
            "user_id": str(user.id),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    return response


@router.post("/logout", response_class=HTMLResponse)
async def logout_post(response: Response):
    """
    Handle logout.
    
    Clears the session cookie and redirects to login page.
    
    Args:
        response: FastAPI response object for clearing cookies
        
    Returns:
        RedirectResponse to login page
    """
    # Clear the access token cookie
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    
    return response


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Dashboard page.
    
    Fetches dashboard data from the dashboard service and renders the template.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with dashboard page
    """
    from api.services.dashboard import get_dashboard_stats
    
    # Fetch dashboard statistics
    stats = await get_dashboard_stats(db)
    
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats.to_dict()
        }
    )


@router.get("/routes", response_class=HTMLResponse)
async def routes_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Routes list page.
    
    Fetches routes from the API and renders the list template.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with routes list page
    """
    from api.repositories.route_subscription_repository import RouteSubscriptionRepository
    
    # Fetch all routes (for now, we'll load all - can add pagination later)
    route_repo = RouteSubscriptionRepository(db)
    routes_list = await route_repo.list_all()
    
    # Convert to dict format for template
    routes = [
        {
            "id": str(route.id),
            "origin_country": route.origin_country,
            "destination_country": route.destination_country,
            "visa_type": route.visa_type,
            "email": route.email,
            "is_active": route.is_active,
            "created_at": route.created_at.isoformat() if route.created_at else None,
            "updated_at": route.updated_at.isoformat() if route.updated_at else None
        }
        for route in routes_list
    ]
    
    return templates.TemplateResponse(
        "pages/routes/list.html",
        {
            "request": request,
            "user": current_user,
            "routes": routes
        }
    )


@router.get("/routes/new", response_class=HTMLResponse)
async def route_new_page(
    request: Request,
    current_user: User = Depends(get_current_user_web)
):
    """
    Create route form page.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        HTMLResponse with route form page (create mode)
    """
    return templates.TemplateResponse(
        "pages/routes/form.html",
        {
            "request": request,
            "user": current_user,
            "route": None
        }
    )


@router.get("/routes/{route_id}", response_class=HTMLResponse)
async def route_edit_page(
    request: Request,
    route_id: str,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Edit route form page.
    
    Fetches route from database and renders form in edit mode.
    
    Args:
        request: FastAPI request object
        route_id: Route subscription UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with route form page (edit mode)
    """
    from uuid import UUID
    from api.repositories.route_subscription_repository import RouteSubscriptionRepository
    
    try:
        route_uuid = UUID(route_id)
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    route_repo = RouteSubscriptionRepository(db)
    route = await route_repo.get_by_id(route_uuid)
    
    if not route:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    # Convert to dict format for template
    route_dict = {
        "id": str(route.id),
        "origin_country": route.origin_country,
        "destination_country": route.destination_country,
        "visa_type": route.visa_type,
        "email": route.email,
        "is_active": route.is_active,
        "created_at": route.created_at.isoformat() if route.created_at else None,
        "updated_at": route.updated_at.isoformat() if route.updated_at else None
    }
    
    return templates.TemplateResponse(
        "pages/routes/form.html",
        {
            "request": request,
            "user": current_user,
            "route": route_dict
        }
    )


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Sources list page.
    
    Fetches sources from the API and renders the list template with status.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with sources list page
    """
    from api.repositories.source_repository import SourceRepository
    from api.services.source import get_source_with_status
    
    # Fetch all sources (for now, we'll load all - can add pagination later)
    source_repo = SourceRepository(db)
    sources_list = await source_repo.list_all()
    
    # Convert to dict format with status for template
    sources = []
    for source in sources_list:
        source_dict = await get_source_with_status(session=db, source=source)
        sources.append(source_dict)
    
    return templates.TemplateResponse(
        "pages/sources/list.html",
        {
            "request": request,
            "user": current_user,
            "sources": sources
        }
    )


@router.get("/sources/new", response_class=HTMLResponse)
async def source_new_page(
    request: Request,
    current_user: User = Depends(get_current_user_web)
):
    """
    Create source form page.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        HTMLResponse with source form page (create mode)
    """
    return templates.TemplateResponse(
        "pages/sources/form.html",
        {
            "request": request,
            "user": current_user,
            "source": None
        }
    )


@router.get("/sources/{source_id}", response_class=HTMLResponse)
async def source_detail_page(
    request: Request,
    source_id: str,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Source detail view page.
    
    Shows source information, status, and recent changes.
    
    Args:
        request: FastAPI request object
        source_id: Source UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with source detail page
    """
    from uuid import UUID
    from api.repositories.source_repository import SourceRepository
    from api.repositories.policy_change_repository import PolicyChangeRepository
    from api.services.source import get_source_with_status
    
    try:
        source_uuid = UUID(source_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_id(source_uuid)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Convert to dict format with status for template
    source_dict = await get_source_with_status(session=db, source=source)
    
    # Add error count if available
    source_dict['consecutive_fetch_failures'] = source.consecutive_fetch_failures
    
    # Get recent changes (last 10)
    change_repo = PolicyChangeRepository(db)
    all_changes = await change_repo.get_by_source_id(source_uuid)
    changes = all_changes[:10]  # Limit to 10 most recent
    
    recent_changes = [
        {
            "id": str(change.id),
            "detected_at": change.detected_at.isoformat() if change.detected_at else None
        }
        for change in changes
    ]
    
    return templates.TemplateResponse(
        "pages/sources/detail.html",
        {
            "request": request,
            "user": current_user,
            "source": source_dict,
            "recent_changes": recent_changes
        }
    )


@router.get("/sources/{source_id}/edit", response_class=HTMLResponse)
async def source_edit_page(
    request: Request,
    source_id: str,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Source edit form page.
    
    Fetches source from database and renders form in edit mode.
    
    Args:
        request: FastAPI request object
        source_id: Source UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with source form page (edit mode)
    """
    from uuid import UUID
    from api.repositories.source_repository import SourceRepository
    from api.services.source import get_source_with_status
    
    try:
        source_uuid = UUID(source_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_id(source_uuid)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Convert to dict format with status for template
    source_dict = await get_source_with_status(session=db, source=source)
    
    return templates.TemplateResponse(
        "pages/sources/form.html",
        {
            "request": request,
            "user": current_user,
            "source": source_dict
        }
    )


@router.get("/changes/{change_id}", response_class=HTMLResponse)
async def change_detail_page(
    request: Request,
    change_id: str,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Change detail page with diff view.
    
    Shows full diff for a specific policy change with navigation controls.
    
    Args:
        request: FastAPI request object
        change_id: PolicyChange UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with change detail page
    """
    from uuid import UUID
    from api.services.change import get_change_detail
    
    try:
        change_uuid = UUID(change_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change not found"
        )
    
    # Get change detail
    change_detail = await get_change_detail(session=db, change_id=change_uuid)
    
    if not change_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change not found"
        )
    
    return templates.TemplateResponse(
        "pages/changes/detail.html",
        {
            "request": request,
            "user": current_user,
            "change": change_detail
        }
    )


@router.get("/changes", response_class=HTMLResponse)
async def changes_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    route_id: Optional[str] = None,
    source_id: Optional[str] = None,
    date_range: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Changes list page.
    
    Fetches changes from the API and renders the list template with filters.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        page: Page number (default: 1)
        route_id: Filter by route UUID (optional)
        source_id: Filter by source UUID (optional)
        date_range: Quick date range filter (optional)
        start_date: Custom start date (optional)
        end_date: Custom end date (optional)
        
    Returns:
        HTMLResponse with changes list page
    """
    from datetime import datetime, timedelta
    from api.repositories.route_subscription_repository import RouteSubscriptionRepository
    from api.repositories.source_repository import SourceRepository
    from api.services.change import get_changes_with_details
    
    # Calculate date range if quick option selected
    start_date_obj = None
    end_date_obj = None
    
    if date_range == "7days":
        end_date_obj = datetime.utcnow()
        start_date_obj = end_date_obj - timedelta(days=7)
    elif date_range == "30days":
        end_date_obj = datetime.utcnow()
        start_date_obj = end_date_obj - timedelta(days=30)
    elif start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date)
        except ValueError:
            pass
    elif end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date)
        except ValueError:
            pass
    
    # Get changes
    changes = await get_changes_with_details(
        session=db,
        route_id=route_id,
        source_id=source_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        page=page,
        page_size=50
    )
    
    # Get routes and sources for filter dropdowns
    route_repo = RouteSubscriptionRepository(db)
    source_repo = SourceRepository(db)
    
    routes_list = await route_repo.list_all()
    sources_list = await source_repo.list_all()
    
    routes = [
        {
            "id": str(route.id),
            "origin_country": route.origin_country,
            "destination_country": route.destination_country,
            "visa_type": route.visa_type
        }
        for route in routes_list
    ]
    
    sources = [
        {
            "id": str(source.id),
            "name": source.name
        }
        for source in sources_list
    ]
    
    # Prepare filters for template
    filters = {
        "route_id": route_id or "",
        "source_id": source_id or "",
        "date_range": date_range or "",
        "start_date": start_date or "",
        "end_date": end_date or ""
    }
    
    return templates.TemplateResponse(
        "pages/changes/list.html",
        {
            "request": request,
            "user": current_user,
            "changes": changes,
            "routes": routes,
            "sources": sources,
            "filters": filters
        }
    )


@router.get("/status", response_class=HTMLResponse)
async def status_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    System status monitoring page.
    
    Displays system health and source monitoring status.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with status page
    """
    from api.services.status import get_system_status
    
    # Get system status
    status_data = await get_system_status(session=db)
    
    return templates.TemplateResponse(
        "pages/status.html",
        {
            "request": request,
            "user": current_user,
            "status": status_data
        }
    )


@router.get("/trigger", response_class=HTMLResponse)
async def trigger_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db)
):
    """
    Manual trigger page.
    
    Displays list of all sources with trigger buttons for manual testing.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse with trigger page
    """
    from api.repositories.source_repository import SourceRepository
    
    # Fetch all sources
    source_repo = SourceRepository(db)
    sources_list = await source_repo.list_all()
    
    # Format sources for template
    sources = []
    for source in sources_list:
        source_dict = {
            "id": str(source.id),
            "name": source.name,
            "url": source.url,
            "country": source.country,
            "visa_type": source.visa_type,
            "fetch_type": source.fetch_type,
            "is_active": source.is_active,
            "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None
        }
        sources.append(source_dict)
    
    return templates.TemplateResponse(
        "pages/trigger.html",
        {
            "request": request,
            "user": current_user,
            "sources": sources
        }
    )

