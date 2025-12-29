"""API routes for route subscriptions."""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from api.models.schemas.route_subscription import (
    RouteSubscriptionCreate,
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

logger = logging.getLogger(__name__)

# Route subscription router
routes_router = APIRouter(prefix="/api/routes", tags=["routes"])

# Source router
sources_router = APIRouter(prefix="/api/sources", tags=["sources"])

# Jobs router
jobs_router = APIRouter(prefix="/api/jobs", tags=["jobs"])


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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedRouteResponse:
    """
    List all route subscriptions with pagination.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of items per page (default: 20, max: 100)
        current_user: Authenticated user (from dependency)
        db: Database session
        
    Returns:
        PaginatedResponse with route subscriptions
    """
    route_repo = RouteSubscriptionRepository(db)
    
    # Get paginated routes
    routes, total = await route_repo.list_paginated(page=page, page_size=page_size)
    
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

