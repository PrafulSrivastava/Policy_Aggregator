"""API routes for route subscriptions."""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from api.models.schemas.route_subscription import (
    RouteSubscriptionCreate,
    RouteSubscriptionUpdate,
    RouteSubscriptionResponse
)
from api.models.schemas.source import (
    SourceCreate,
    SourceUpdate,
    SourceResponse
)
from api.models.db.user import User
from api.middleware.auth import get_current_user
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.repositories.source_repository import SourceRepository
from api.services.fetcher_manager import fetch_and_process_source, PipelineResult
from api.services.scheduler import run_daily_fetch_job, JobResult
from api.services.dashboard import get_dashboard_stats
from api.services.status import get_system_status

logger = logging.getLogger(__name__)

# Dashboard router
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Route subscription router
routes_router = APIRouter(prefix="/api/routes", tags=["routes"])

# Source router
sources_router = APIRouter(prefix="/api/sources", tags=["sources"])

# Jobs router
jobs_router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Changes router
changes_router = APIRouter(prefix="/api/changes", tags=["changes"])

# Status router
status_router = APIRouter(prefix="/api/status", tags=["status"])


# ============================================================================
# Dashboard Endpoint
# ============================================================================

@dashboard_router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
    description="Retrieve dashboard statistics including route counts, source counts, recent changes, and source health. Requires authentication.",
    responses={
        200: {
            "description": "Dashboard statistics",
            "content": {
                "application/json": {
                    "example": {
                        "totalRoutes": 5,
                        "totalSources": 10,
                        "activeSources": 8,
                        "changesLast7Days": 3,
                        "changesLast30Days": 12,
                        "recentChanges": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "sourceId": "123e4567-e89b-12d3-a456-426614174001",
                                "sourceName": "Germany Student Visa",
                                "route": "DE: Student",
                                "detectedAt": "2025-01-27T10:00:00Z",
                                "hasDiff": True,
                                "diffLength": 150
                            }
                        ],
                        "sourceHealth": [
                            {
                                "sourceId": "123e4567-e89b-12d3-a456-426614174001",
                                "sourceName": "Germany Student Visa",
                                "country": "DE",
                                "visaType": "Student",
                                "lastCheckedAt": "2025-01-27T10:00:00Z",
                                "status": "healthy",
                                "consecutiveFailures": 0,
                                "lastError": None
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get dashboard statistics.
    
    Args:
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Dictionary with dashboard statistics
    """
    stats = await get_dashboard_stats(db)
    return stats.to_dict()


class PaginatedRouteResponse(BaseModel):
    """Paginated response model for routes."""
    items: List[RouteSubscriptionResponse]
    total: int
    page: int
    page_size: int


class PaginatedSourceResponse(BaseModel):
    """Paginated response model for sources."""
    items: List[SourceResponse]
    total: int
    page: int
    page_size: int


@routes_router.get(
    "",
    response_model=PaginatedRouteResponse,
    status_code=status.HTTP_200_OK,
    summary="List route subscriptions",
    description="Retrieve a paginated list of all route subscriptions. Requires authentication.",
    responses={
        200: {
            "description": "Successfully retrieved route subscriptions",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "origin_country": "IN",
                                "destination_country": "DE",
                                "visa_type": "Student",
                                "email": "user@example.com",
                                "is_active": True,
                                "created_at": "2025-01-27T10:00:00Z",
                                "updated_at": "2025-01-27T10:00:00Z"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 20
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def list_routes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    origin_country: Optional[str] = Query(None, description="Filter by origin country code (2 characters)"),
    destination_country: Optional[str] = Query(None, description="Filter by destination country code (2 characters)"),
    visa_type: Optional[str] = Query(None, description="Filter by visa type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedRouteResponse:
    """
    List all route subscriptions with pagination and optional filtering.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of items per page (default: 20, max: 100)
        origin_country: Filter by origin country code (optional)
        destination_country: Filter by destination country code (optional)
        visa_type: Filter by visa type (optional)
        is_active: Filter by active status (optional)
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        PaginatedResponse with route subscriptions
    """
    route_repo = RouteSubscriptionRepository(db)
    
    # Get paginated routes with filters
    routes, total = await route_repo.list_paginated(
        page=page,
        page_size=page_size,
        origin_country=origin_country,
        destination_country=destination_country,
        visa_type=visa_type,
        is_active=is_active
    )
    
    return PaginatedRouteResponse(
        items=[RouteSubscriptionResponse.model_validate(route) for route in routes],
        total=total,
        page=page,
        page_size=page_size
    )


@routes_router.post(
    "",
    response_model=RouteSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create route subscription",
    description="Create a new route subscription. Requires authentication. Duplicate routes will be rejected.",
    responses={
        201: {
            "description": "Route subscription created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "origin_country": "IN",
                        "destination_country": "DE",
                        "visa_type": "Student",
                        "email": "user@example.com",
                        "is_active": True,
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T10:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Bad Request - Validation error"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        409: {"description": "Conflict - Duplicate route subscription exists"}
    }
)
async def create_route(
    route_data: RouteSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RouteSubscriptionResponse:
    """
    Create a new route subscription.
    
    Args:
        route_data: Route subscription data
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Created route subscription
        
    Raises:
        HTTPException: 409 if duplicate route exists, 400 for validation errors
    """
    route_repo = RouteSubscriptionRepository(db)
    
    # Check for duplicate route
    exists = await route_repo.exists(
        origin=route_data.origin_country,
        destination=route_data.destination_country,
        visa_type=route_data.visa_type,
        email=route_data.email
    )
    
    if exists:
        logger.warning(
            f"Duplicate route subscription attempt: "
            f"{route_data.origin_country} -> {route_data.destination_country}, "
            f"{route_data.visa_type}, {route_data.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_ROUTE",
                "message": "A route subscription with these parameters already exists",
                "details": {
                    "origin_country": route_data.origin_country,
                    "destination_country": route_data.destination_country,
                    "visa_type": route_data.visa_type,
                    "email": route_data.email
                }
            }
        )
    
    # Create route subscription
    try:
        route = await route_repo.create(route_data.model_dump())
        logger.info(
            f"Created route subscription: {route.id}",
            extra={
                "route_id": str(route.id),
                "origin_country": route.origin_country,
                "destination_country": route.destination_country,
                "visa_type": route.visa_type,
                "user_id": str(current_user.id)
            }
        )
        return RouteSubscriptionResponse.model_validate(route)
    except IntegrityError as e:
        logger.error(f"Database integrity error creating route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_ROUTE",
                "message": "A route subscription with these parameters already exists"
            }
        )


@routes_router.get(
    "/{route_id}",
    response_model=RouteSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get route subscription",
    description="Retrieve a specific route subscription by ID. Requires authentication.",
    responses={
        200: {
            "description": "Route subscription found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "origin_country": "IN",
                        "destination_country": "DE",
                        "visa_type": "Student",
                        "email": "user@example.com",
                        "is_active": True,
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Route subscription not found"}
    }
)
async def get_route(
    route_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RouteSubscriptionResponse:
    """
    Get a specific route subscription by ID.
    
    Args:
        route_id: Route subscription UUID
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Route subscription data
        
    Raises:
        HTTPException: 404 if route not found
    """
    route_repo = RouteSubscriptionRepository(db)
    route = await route_repo.get_by_id(route_id)
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ROUTE_NOT_FOUND",
                "message": f"Route subscription with id {route_id} not found"
            }
        )
    
        return RouteSubscriptionResponse.model_validate(route)


@routes_router.put(
    "/{route_id}",
    response_model=RouteSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update route subscription",
    description="Update a route subscription. Requires authentication. Supports partial updates.",
    responses={
        200: {
            "description": "Route subscription updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "origin_country": "IN",
                        "destination_country": "DE",
                        "visa_type": "Student",
                        "email": "user@example.com",
                        "is_active": True,
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T11:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Bad Request - Validation error"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Route subscription not found"}
    }
)
async def update_route(
    route_id: UUID,
    route_data: RouteSubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RouteSubscriptionResponse:
    """
    Update a route subscription.
    
    Args:
        route_id: Route subscription UUID
        route_data: Route subscription update data (partial updates supported)
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Updated route subscription
        
    Raises:
        HTTPException: 404 if route not found, 400 for validation errors
    """
    route_repo = RouteSubscriptionRepository(db)
    
    # Get route to check if exists
    route = await route_repo.get_by_id(route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ROUTE_NOT_FOUND",
                "message": f"Route subscription with id {route_id} not found"
            }
        )
    
    # Prepare update data (only include non-None fields)
    update_data = route_data.model_dump(exclude_unset=True)
    
    if not update_data:
        # No fields to update, return existing route
        return RouteSubscriptionResponse.model_validate(route)
    
    # Update route subscription
    try:
        updated_route = await route_repo.update(route_id, update_data)
        logger.info(
            f"Updated route subscription: {route_id}",
            extra={
                "route_id": str(route_id),
                "updated_fields": list(update_data.keys()),
                "user_id": str(current_user.id)
            }
        )
        return RouteSubscriptionResponse.model_validate(updated_route)
    except ValueError as e:
        logger.error(f"Error updating route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ROUTE_NOT_FOUND",
                "message": str(e)
            }
        )


@routes_router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete route subscription",
    description="Delete a route subscription by ID. Requires authentication.",
    responses={
        204: {"description": "Route subscription deleted successfully"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Route subscription not found"}
    }
)
async def delete_route(
    route_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a route subscription.
    
    Args:
        route_id: Route subscription UUID
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Raises:
        HTTPException: 404 if route not found
    """
    route_repo = RouteSubscriptionRepository(db)
    deleted = await route_repo.delete(route_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ROUTE_NOT_FOUND",
                "message": f"Route subscription with id {route_id} not found"
            }
        )
    
    logger.info(
        f"Deleted route subscription: {route_id}",
        extra={
            "route_id": str(route_id),
            "user_id": str(current_user.id)
        }
    )


# ============================================================================
# Source Endpoints
# ============================================================================

@sources_router.get(
    "",
    response_model=PaginatedSourceResponse,
    status_code=status.HTTP_200_OK,
    summary="List sources",
    description="Retrieve a paginated list of sources with optional filtering. Requires authentication.",
    responses={
        200: {
            "description": "Successfully retrieved sources",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "country": "DE",
                                "visa_type": "Student",
                                "url": "https://example.com/policy",
                                "name": "Germany Student Visa Source",
                                "fetch_type": "html",
                                "check_frequency": "daily",
                                "is_active": True,
                                "metadata": {},
                                "last_checked_at": None,
                                "last_change_detected_at": None,
                                "created_at": "2025-01-27T10:00:00Z",
                                "updated_at": "2025-01-27T10:00:00Z"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 20
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def list_sources(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    country: str = Query(None, description="Filter by country code (2 characters)"),
    visa_type: str = Query(None, description="Filter by visa type"),
    is_active: bool = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedSourceResponse:
    """
    List all sources with pagination and optional filtering.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of items per page (default: 20, max: 100)
        country: Filter by country code (optional)
        visa_type: Filter by visa type (optional)
        is_active: Filter by active status (optional)
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        PaginatedSourceResponse with sources
    """
    source_repo = SourceRepository(db)
    
    # Get paginated sources with filters
    sources, total = await source_repo.list_paginated(
        page=page,
        page_size=page_size,
        country=country,
        visa_type=visa_type,
        is_active=is_active
    )
    
    return PaginatedSourceResponse(
        items=[SourceResponse.model_validate(source) for source in sources],
        total=total,
        page=page,
        page_size=page_size
    )


@sources_router.post(
    "",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create source",
    description="Create a new source. Requires authentication. Duplicate sources will be rejected.",
    responses={
        201: {
            "description": "Source created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "country": "DE",
                        "visa_type": "Student",
                        "url": "https://example.com/policy",
                        "name": "Germany Student Visa Source",
                        "fetch_type": "html",
                        "check_frequency": "daily",
                        "is_active": True,
                        "metadata": {},
                        "last_checked_at": None,
                        "last_change_detected_at": None,
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T10:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Bad Request - Validation error"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        409: {"description": "Conflict - Duplicate source exists"}
    }
)
async def create_source(
    source_data: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SourceResponse:
    """
    Create a new source.
    
    Args:
        source_data: Source data
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Created source
        
    Raises:
        HTTPException: 409 if duplicate source exists, 400 for validation errors
    """
    source_repo = SourceRepository(db)
    
    # Check for duplicate source
    exists = await source_repo.exists(
        url=source_data.url,
        country=source_data.country,
        visa_type=source_data.visa_type
    )
    
    if exists:
        logger.warning(
            f"Duplicate source attempt: {source_data.url}, "
            f"{source_data.country}, {source_data.visa_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_SOURCE",
                "message": "A source with these parameters already exists",
                "details": {
                    "url": source_data.url,
                    "country": source_data.country,
                    "visa_type": source_data.visa_type
                }
            }
        )
    
    # Create source
    try:
        source = await source_repo.create(source_data.model_dump())
        logger.info(
            f"Created source: {source.id}",
            extra={
                "source_id": str(source.id),
                "country": source.country,
                "visa_type": source.visa_type,
                "url": source.url,
                "fetch_type": source.fetch_type,
                "user_id": str(current_user.id)
            }
        )
        return SourceResponse.model_validate(source)
    except IntegrityError as e:
        logger.error(f"Database integrity error creating source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_SOURCE",
                "message": "A source with these parameters already exists"
            }
        )


@sources_router.get(
    "/{source_id}",
    response_model=SourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get source",
    description="Retrieve a specific source by ID with metadata. Requires authentication.",
    responses={
        200: {
            "description": "Source found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "country": "DE",
                        "visa_type": "Student",
                        "url": "https://example.com/policy",
                        "name": "Germany Student Visa Source",
                        "fetch_type": "html",
                        "check_frequency": "daily",
                        "is_active": True,
                        "metadata": {},
                        "last_checked_at": None,
                        "last_change_detected_at": None,
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Source not found"}
    }
)
async def get_source(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SourceResponse:
    """
    Get a specific source by ID.
    
    Args:
        source_id: Source UUID
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Source data with metadata
        
    Raises:
        HTTPException: 404 if source not found
    """
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_id(source_id)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source with id {source_id} not found"
            }
        )
    
    return SourceResponse.model_validate(source)


@sources_router.put(
    "/{source_id}",
    response_model=SourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update source",
    description="Update a source configuration. Requires authentication. Supports partial updates.",
    responses={
        200: {
            "description": "Source updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "country": "DE",
                        "visa_type": "Student",
                        "url": "https://updated.com/policy",
                        "name": "Updated Source Name",
                        "fetch_type": "html",
                        "check_frequency": "weekly",
                        "is_active": False,
                        "metadata": {},
                        "last_checked_at": None,
                        "last_change_detected_at": None,
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T11:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Bad Request - Validation error"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Source not found"}
    }
)
async def update_source(
    source_id: UUID,
    source_data: SourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SourceResponse:
    """
    Update a source configuration.
    
    Args:
        source_id: Source UUID
        source_data: Source update data (partial updates supported)
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Updated source data
        
    Raises:
        HTTPException: 404 if source not found, 400 for validation errors
    """
    source_repo = SourceRepository(db)
    
    # Get source to check if exists
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source with id {source_id} not found"
            }
        )
    
    # Prepare update data (only include non-None fields)
    update_data = source_data.model_dump(exclude_unset=True)
    
    if not update_data:
        # No fields to update, return existing source
        return SourceResponse.model_validate(source)
    
        # Update source
    try:
        updated_source = await source_repo.update(source_id, update_data)
        logger.info(
            f"Updated source: {source_id}",
            extra={
                "source_id": str(source_id),
                "updated_fields": list(update_data.keys()),
                "user_id": str(current_user.id)
            }
        )
        return SourceResponse.model_validate(updated_source)
    except ValueError as e:
        logger.error(f"Error updating source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SOURCE_NOT_FOUND",
                "message": str(e)
            }
        )


@sources_router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete source",
    description="Delete a source by ID. Cascade delete will remove related PolicyVersions and PolicyChanges. Requires authentication.",
    responses={
        204: {"description": "Source deleted successfully"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Source not found"}
    }
)
async def delete_source(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a source.
    
    Cascade delete is handled by the database (PolicyVersions and PolicyChanges will be automatically deleted).
    
    Args:
        source_id: Source UUID
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Raises:
        HTTPException: 404 if source not found
    """
    source_repo = SourceRepository(db)
    deleted = await source_repo.delete(source_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source with id {source_id} not found"
            }
        )
    
    logger.info(
        f"Deleted source: {source_id}",
        extra={
            "source_id": str(source_id),
            "user_id": str(current_user.id)
        }
    )


@sources_router.post(
    "/{source_id}/trigger",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Trigger fetch and process pipeline",
    description="Manually trigger the fetch and process pipeline for a specific source. Requires authentication.",
    responses={
        200: {
            "description": "Pipeline execution result",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "sourceId": "123e4567-e89b-12d3-a456-426614174000",
                        "changeDetected": False,
                        "policyVersionId": "123e4567-e89b-12d3-a456-426614174001",
                        "policyChangeId": None,
                        "error": None,
                        "fetchedAt": "2025-01-27T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Source not found"}
    }
)
async def trigger_source_fetch(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Manually trigger the fetch and process pipeline for a source.
    
    This endpoint executes the complete pipeline:
    - Fetches content from the source
    - Normalizes the content
    - Detects changes
    - Stores PolicyVersion
    - Creates PolicyChange if change detected
    
    Args:
        source_id: Source UUID to fetch and process
        current_user: Authenticated user (from dependency)
        db: Database session
    
    Returns:
        PipelineResult as JSON with success status, change detection, and error information
    
    Raises:
        HTTPException: 404 if source not found
    """
    # Verify source exists
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_id(source_id)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source with id {source_id} not found"
            }
        )
    
    # Execute pipeline
    logger.info(
        f"Manual pipeline trigger for source {source_id} by user {current_user.id}"
    )
    
    result = await fetch_and_process_source(session=db, source_id=source_id)
    
    # Convert PipelineResult to dict for JSON response
    response_data = {
        "success": result.success,
        "sourceId": str(result.source_id),
        "changeDetected": result.change_detected,
        "policyVersionId": str(result.policy_version_id) if result.policy_version_id else None,
        "policyChangeId": str(result.policy_change_id) if result.policy_change_id else None,
        "error": result.error_message,
        "fetchedAt": result.fetched_at.isoformat() if result.fetched_at else None
    }
    
    if result.success:
        logger.info(
            f"Pipeline completed for source {source_id}: "
            f"change_detected={result.change_detected}, "
            f"version_id={result.policy_version_id}"
        )
    else:
        logger.warning(
            f"Pipeline failed for source {source_id}: {result.error_message}"
        )
    
    return response_data


@jobs_router.post(
    "/daily-fetch",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Trigger daily fetch job",
    description="Manually trigger the daily fetch job that processes all active sources with daily check frequency. Requires authentication.",
    responses={
        200: {
            "description": "Job execution result",
            "content": {
                "application/json": {
                    "example": {
                        "startedAt": "2025-01-27T10:00:00Z",
                        "completedAt": "2025-01-27T10:05:00Z",
                        "sourcesProcessed": 5,
                        "sourcesSucceeded": 4,
                        "sourcesFailed": 1,
                        "changesDetected": 2,
                        "alertsSent": 3,
                        "errors": []
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def trigger_daily_fetch_job(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Manually trigger the daily fetch job.
    
    This endpoint executes the complete daily fetch job:
    - Gets all active sources with daily check_frequency
    - Runs fetch pipeline for each source
    - Triggers alert engine when changes are detected
    - Handles errors gracefully (one source failure doesn't stop others)
    
    Args:
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        JobResult as JSON with summary of job execution
    """
    logger.info(
        f"Manual daily fetch job trigger by user {current_user.id}"
    )
    
    # Execute daily fetch job
    job_result: JobResult = await run_daily_fetch_job(session=db)
    
    # Convert JobResult to dict for JSON response
    response_data = {
        "startedAt": job_result.started_at.isoformat(),
        "completedAt": job_result.completed_at.isoformat() if job_result.completed_at else None,
        "sourcesProcessed": job_result.sources_processed,
        "sourcesSucceeded": job_result.sources_succeeded,
        "sourcesFailed": job_result.sources_failed,
        "changesDetected": job_result.changes_detected,
        "alertsSent": job_result.alerts_sent,
        "errors": job_result.errors
    }
    
    logger.info(
        f"Daily fetch job completed: "
        f"{job_result.sources_processed} processed, "
        f"{job_result.changes_detected} changes detected"
    )
    
    return response_data


# ============================================================================
# Status Endpoints
# ============================================================================

@status_router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get system status",
    description="Retrieve comprehensive system status including all sources with health information, statistics, and monitoring data. Requires authentication.",
    responses={
        200: {
            "description": "System status data",
            "content": {
                "application/json": {
                    "example": {
                        "sources": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "name": "Germany Student Visa Source",
                                "country": "DE",
                                "visa_type": "Student",
                                "url": "https://example.com/policy",
                                "fetch_type": "html",
                                "check_frequency": "daily",
                                "is_active": True,
                                "last_checked_at": "2025-01-27T10:00:00Z",
                                "last_change_detected_at": "2025-01-26T10:00:00Z",
                                "status": "active",
                                "consecutive_fetch_failures": 0,
                                "last_fetch_error": None,
                                "next_check_time": "2025-01-28T10:00:00Z"
                            }
                        ],
                        "statistics": {
                            "total_sources": 10,
                            "healthy_sources": 8,
                            "error_sources": 1,
                            "stale_sources": 1,
                            "never_checked_sources": 0
                        },
                        "last_daily_job_run": None
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def get_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get comprehensive system status.
    
    Args:
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Dictionary with system status data including sources, statistics, and monitoring info
    """
    status_data = await get_system_status(session=db)
    return status_data


# ============================================================================
# Changes Endpoints
# ============================================================================

@changes_router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List policy changes",
    description="Retrieve a paginated list of policy changes with optional filtering. Requires authentication.",
    responses={
        200: {
            "description": "Successfully retrieved changes",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "detected_at": "2025-01-27T10:00:00Z",
                                "source": {
                                    "id": "456e7890-e89b-12d3-a456-426614174000",
                                    "name": "Germany Student Visa Source",
                                    "country": "DE",
                                    "visa_type": "Student"
                                },
                                "route": {
                                    "id": "789e0123-e89b-12d3-a456-426614174000",
                                    "origin_country": "IN",
                                    "destination_country": "DE",
                                    "visa_type": "Student",
                                    "display": "IN → DE, Student"
                                },
                                "summary": "Content changed",
                                "is_new": True,
                                "diff_length": 150
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 50,
                        "pages": 1
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def list_changes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page (max 100)"),
    route_id: Optional[str] = Query(None, description="Filter by route subscription UUID"),
    source_id: Optional[str] = Query(None, description="Filter by source UUID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    sort_by: str = Query("detected_at", description="Column to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    List all policy changes with pagination and optional filtering.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of items per page (default: 50, max: 100)
        route_id: Filter by route subscription UUID (optional)
        source_id: Filter by source UUID (optional)
        start_date: Filter by start date in ISO format (optional)
        end_date: Filter by end date in ISO format (optional)
        sort_by: Column to sort by (default: "detected_at")
        sort_order: Sort order "asc" or "desc" (default: "desc")
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Dictionary with paginated changes and metadata
    """
    from datetime import datetime
    from api.services.change import get_changes_with_details
    
    # Parse date strings
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid start_date format: {start_date}")
    
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid end_date format: {end_date}")
    
    # Get changes
    result = await get_changes_with_details(
        session=db,
        route_id=route_id,
        source_id=source_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return result


@changes_router.get(
    "/{change_id}",
    status_code=status.HTTP_200_OK,
    summary="Get change detail",
    description="Retrieve detailed information for a specific policy change including diff, versions, and navigation. Requires authentication.",
    responses={
        200: {
            "description": "Change detail found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "detected_at": "2025-01-27T10:00:00Z",
                        "diff": "--- old\n+++ new\n...",
                        "diff_length": 150,
                        "source": {
                            "id": "456e7890-e89b-12d3-a456-426614174000",
                            "name": "Germany Student Visa Source",
                            "url": "https://example.com/policy",
                            "country": "DE",
                            "visa_type": "Student"
                        },
                        "route": {
                            "id": "789e0123-e89b-12d3-a456-426614174000",
                            "origin_country": "IN",
                            "destination_country": "DE",
                            "visa_type": "Student",
                            "display": "IN → DE, Student"
                        },
                        "old_version": {
                            "id": "abc123...",
                            "content_hash": "...",
                            "raw_text": "...",
                            "fetched_at": "2025-01-26T10:00:00Z",
                            "content_length": 1000
                        },
                        "new_version": {
                            "id": "def456...",
                            "content_hash": "...",
                            "raw_text": "...",
                            "fetched_at": "2025-01-27T10:00:00Z",
                            "content_length": 1200
                        },
                        "previous_change_id": "111e2222-e89b-12d3-a456-426614174000",
                        "next_change_id": "333e4444-e89b-12d3-a456-426614174000"
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Change not found"}
    }
)
async def get_change_detail(
    change_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get detailed information for a specific policy change.
    
    Args:
        change_id: PolicyChange UUID
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Dictionary with detailed change information
        
    Raises:
        HTTPException: 404 if change not found
    """
    from api.services.change import get_change_detail as get_change_detail_service
    
    change_detail = await get_change_detail_service(session=db, change_id=change_id)
    
    if not change_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CHANGE_NOT_FOUND",
                "message": f"Policy change with id {change_id} not found"
            }
        )
    
    return change_detail


@changes_router.get(
    "/{change_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download change diff",
    description="Download the diff text for a specific policy change as a plain text file. Requires authentication.",
    responses={
        200: {
            "description": "Diff text file",
            "content": {
                "text/plain": {}
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not Found - Change not found"}
    }
)
async def download_change_diff(
    change_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download the diff text for a policy change as a plain text file.
    
    Args:
        change_id: PolicyChange UUID
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        Plain text file response with diff content
        
    Raises:
        HTTPException: 404 if change not found
    """
    from fastapi.responses import Response
    from datetime import datetime
    from api.services.change import get_change_detail as get_change_detail_service
    
    change_detail = await get_change_detail_service(session=db, change_id=change_id)
    
    if not change_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CHANGE_NOT_FOUND",
                "message": f"Policy change with id {change_id} not found"
            }
        )
    
    # Get diff text
    diff_text = change_detail.get("diff", "")
    source_name = change_detail.get("source", {}).get("name", "unknown")
    detected_at = change_detail.get("detected_at", "")
    
    # Create filename with timestamp and source name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"diff_{source_name.replace(' ', '_')}_{timestamp}.txt"
    
    # Create response with diff text
    return Response(
        content=diff_text,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@changes_router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    summary="Export changes to CSV",
    description="Export filtered policy changes to CSV format. Requires authentication.",
    responses={
        200: {
            "description": "CSV file with changes",
            "content": {
                "text/csv": {}
            }
        },
        401: {"description": "Unauthorized - Missing or invalid authentication token"}
    }
)
async def export_changes(
    route_id: Optional[str] = Query(None, description="Filter by route subscription UUID"),
    source_id: Optional[str] = Query(None, description="Filter by source UUID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export policy changes to CSV format.
    
    Args:
        route_id: Filter by route subscription UUID (optional)
        source_id: Filter by source UUID (optional)
        start_date: Filter by start date in ISO format (optional)
        end_date: Filter by end date in ISO format (optional)
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        CSV file response with all matching changes
    """
    from datetime import datetime
    from fastapi.responses import Response
    from api.services.change import get_changes_with_details
    import csv
    import io
    
    # Parse date strings
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid start_date format: {start_date}")
    
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid end_date format: {end_date}")
    
    # Get all changes (no pagination for export)
    result = await get_changes_with_details(
        session=db,
        route_id=route_id,
        source_id=source_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        page=1,
        page_size=10000,  # Large page size for export
        sort_by="detected_at",
        sort_order="desc"
    )
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Detected At",
        "Source Name",
        "Source Country",
        "Source Visa Type",
        "Route",
        "Change Summary",
        "Diff Length"
    ])
    
    # Write data rows
    for change in result["items"]:
        route_display = change["route"]["display"] if change["route"] else "No route"
        writer.writerow([
            change["detected_at"] or "",
            change["source"]["name"],
            change["source"]["country"],
            change["source"]["visa_type"],
            route_display,
            change["summary"],
            change["diff_length"]
        ])
    
    # Create response
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=policy_changes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

