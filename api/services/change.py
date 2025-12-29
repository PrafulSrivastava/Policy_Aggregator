"""Change history service for retrieving and formatting policy changes."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import selectinload

from api.models.db.policy_change import PolicyChange
from api.models.db.source import Source
from api.models.db.route_subscription import RouteSubscription
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.services.route_mapper import RouteMapper

logger = logging.getLogger(__name__)

# Maximum diff length for summary (characters)
MAX_SUMMARY_LENGTH = 100
# Large diff threshold (if diff is larger, show generic message)
LARGE_DIFF_THRESHOLD = 500


def generate_change_summary(diff: str) -> str:
    """
    Generate a summary from diff text.
    
    Args:
        diff: Diff text (unified diff format)
        
    Returns:
        Summary string (first line or "Content changed" if too large)
    """
    if not diff:
        return "Content changed"
    
    # If diff is very large, show generic message
    if len(diff) > LARGE_DIFF_THRESHOLD:
        return "Content changed"
    
    # Extract first line of diff
    lines = diff.split('\n')
    if lines:
        first_line = lines[0].strip()
        if first_line:
            # Truncate if too long
            if len(first_line) > MAX_SUMMARY_LENGTH:
                return first_line[:MAX_SUMMARY_LENGTH] + "..."
            return first_line
    
    return "Content changed"


async def get_changes_with_details(
    session: AsyncSession,
    route_id: Optional[str] = None,
    source_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "detected_at",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    Get policy changes with route and source information.
    
    Args:
        session: Database session
        route_id: Optional route UUID to filter by
        source_id: Optional source UUID to filter by
        start_date: Optional start date for date range filter
        end_date: Optional end date for date range filter
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_by: Column to sort by (default: "detected_at")
        sort_order: Sort order ("asc" or "desc", default: "desc")
        
    Returns:
        Dictionary with paginated changes and metadata:
        {
            "items": [change_dict, ...],
            "total": int,
            "page": int,
            "page_size": int,
            "pages": int
        }
    """
    from uuid import UUID
    
    change_repo = PolicyChangeRepository(session)
    source_repo = SourceRepository(session)
    route_repo = RouteSubscriptionRepository(session)
    route_mapper = RouteMapper(session)
    
    # Build query
    query = select(PolicyChange).options(selectinload(PolicyChange.source))
    
    # Apply filters
    filters = []
    
    if source_id:
        try:
            source_uuid = UUID(source_id)
            filters.append(PolicyChange.source_id == source_uuid)
        except ValueError:
            logger.warning(f"Invalid source_id: {source_id}")
    
    if route_id:
        try:
            route_uuid = UUID(route_id)
            # Get sources for this route
            sources = await route_mapper.get_sources_for_route_id(route_uuid)
            if sources:
                source_ids = [source.id for source in sources]
                filters.append(PolicyChange.source_id.in_(source_ids))
            else:
                # No sources for this route, return empty result
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "pages": 0
                }
        except ValueError:
            logger.warning(f"Invalid route_id: {route_id}")
        except Exception as e:
            logger.error(f"Error getting sources for route: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "pages": 0
            }
    
    if start_date:
        filters.append(PolicyChange.detected_at >= start_date)
    
    if end_date:
        # Add one day to make end_date inclusive
        end_date_inclusive = end_date + timedelta(days=1)
        filters.append(PolicyChange.detected_at < end_date_inclusive)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply sorting
    if sort_by == "detected_at":
        if sort_order == "asc":
            query = query.order_by(PolicyChange.detected_at)
        else:
            query = query.order_by(desc(PolicyChange.detected_at))
    else:
        # Default to detected_at desc
        query = query.order_by(desc(PolicyChange.detected_at))
    
    # Get total count
    count_query = select(func.count()).select_from(PolicyChange)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await session.execute(query)
    changes = list(result.scalars().all())
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    # Format changes with route and source information
    items = []
    for change in changes:
        # Get source
        source = change.source
        
        # Get routes for this source
        routes = await route_mapper.get_routes_for_source(source)
        
        # Format route information
        route_info = None
        if routes:
            # Use first route (or could show all)
            route = routes[0]
            route_info = {
                "id": str(route.id),
                "origin_country": route.origin_country,
                "destination_country": route.destination_country,
                "visa_type": route.visa_type,
                "display": f"{route.origin_country} → {route.destination_country}, {route.visa_type}"
            }
        
        # Generate summary
        summary = generate_change_summary(change.diff)
        
        # Check if change is new (within last 24 hours)
        is_new = False
        if change.detected_at:
            time_since = datetime.utcnow() - change.detected_at.replace(tzinfo=None)
            is_new = time_since < timedelta(hours=24)
        
        change_dict = {
            "id": str(change.id),
            "detected_at": change.detected_at.isoformat() if change.detected_at else None,
            "source": {
                "id": str(source.id),
                "name": source.name,
                "country": source.country,
                "visa_type": source.visa_type
            },
            "route": route_info,
            "summary": summary,
            "is_new": is_new,
            "diff_length": change.diff_length
        }
        items.append(change_dict)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


async def get_change_detail(
    session: AsyncSession,
    change_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a specific policy change.
    
    Args:
        session: Database session
        change_id: PolicyChange UUID
        
    Returns:
        Dictionary with detailed change information including:
        - Change metadata (id, detected_at, diff, etc.)
        - Source information (name, url, country, visa_type)
        - Route information (origin → destination, visa_type)
        - Old and new PolicyVersion content
        - Previous and next change IDs for navigation
        None if change not found
    """
    from uuid import UUID
    
    change_repo = PolicyChangeRepository(session)
    route_mapper = RouteMapper(session)
    
    # Fetch change with all relationships loaded
    change = await session.execute(
        select(PolicyChange)
        .options(
            selectinload(PolicyChange.source),
            selectinload(PolicyChange.old_version),
            selectinload(PolicyChange.new_version)
        )
        .where(PolicyChange.id == change_id)
    )
    change = change.scalar_one_or_none()
    
    if not change:
        return None
    
    # Get source
    source = change.source
    
    # Get routes for this source
    routes = await route_mapper.get_routes_for_source(source)
    
    # Format route information
    route_info = None
    if routes:
        # Use first route (or could show all)
        route = routes[0]
        route_info = {
            "id": str(route.id),
            "origin_country": route.origin_country,
            "destination_country": route.destination_country,
            "visa_type": route.visa_type,
            "display": f"{route.origin_country} → {route.destination_country}, {route.visa_type}"
        }
    
    # Get old and new version content
    old_version_info = None
    if change.old_version:
        old_version_info = {
            "id": str(change.old_version.id),
            "content_hash": change.old_version.content_hash,
            "raw_text": change.old_version.raw_text,
            "fetched_at": change.old_version.fetched_at.isoformat() if change.old_version.fetched_at else None,
            "content_length": change.old_version.content_length
        }
    
    new_version_info = None
    if change.new_version:
        new_version_info = {
            "id": str(change.new_version.id),
            "content_hash": change.new_version.content_hash,
            "raw_text": change.new_version.raw_text,
            "fetched_at": change.new_version.fetched_at.isoformat() if change.new_version.fetched_at else None,
            "content_length": change.new_version.content_length
        }
    
    # Get previous and next changes for navigation
    # Previous = change detected before this one (descending order)
    # Next = change detected after this one (ascending order)
    previous_change = None
    next_change = None
    
    if change.detected_at:
        # Get previous change (detected before this one, same source)
        prev_result = await session.execute(
            select(PolicyChange)
            .where(
                and_(
                    PolicyChange.source_id == change.source_id,
                    PolicyChange.detected_at < change.detected_at
                )
            )
            .order_by(desc(PolicyChange.detected_at))
            .limit(1)
        )
        prev_change = prev_result.scalar_one_or_none()
        if prev_change:
            previous_change = str(prev_change.id)
        
        # Get next change (detected after this one, same source)
        next_result = await session.execute(
            select(PolicyChange)
            .where(
                and_(
                    PolicyChange.source_id == change.source_id,
                    PolicyChange.detected_at > change.detected_at
                )
            )
            .order_by(PolicyChange.detected_at)
            .limit(1)
        )
        next_change_obj = next_result.scalar_one_or_none()
        if next_change_obj:
            next_change = str(next_change_obj.id)
    
    return {
        "id": str(change.id),
        "detected_at": change.detected_at.isoformat() if change.detected_at else None,
        "diff": change.diff,
        "diff_length": change.diff_length,
        "old_hash": change.old_hash,
        "new_hash": change.new_hash,
        "alert_sent_at": change.alert_sent_at.isoformat() if change.alert_sent_at else None,
        "created_at": change.created_at.isoformat() if change.created_at else None,
        "source": {
            "id": str(source.id),
            "name": source.name,
            "url": source.url,
            "country": source.country,
            "visa_type": source.visa_type
        },
        "route": route_info,
        "old_version": old_version_info,
        "new_version": new_version_info,
        "previous_change_id": previous_change,
        "next_change_id": next_change
    }
