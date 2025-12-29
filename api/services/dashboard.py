"""Dashboard service for aggregating statistics."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.repositories.source_repository import SourceRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.models.db.source import Source
from api.models.db.policy_change import PolicyChange

logger = logging.getLogger(__name__)


class DashboardStats:
    """Dashboard statistics data model."""
    
    def __init__(
        self,
        total_routes: int,
        total_sources: int,
        active_sources: int,
        changes_last_7_days: int,
        changes_last_30_days: int,
        recent_changes: List[Dict[str, Any]],
        source_health: List[Dict[str, Any]],
        route_statistics: List[Dict[str, Any]] = None
    ):
        self.total_routes = total_routes
        self.total_sources = total_sources
        self.active_sources = active_sources
        self.changes_last_7_days = changes_last_7_days
        self.changes_last_30_days = changes_last_30_days
        self.recent_changes = recent_changes
        self.source_health = source_health
        self.route_statistics = route_statistics or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "totalRoutes": self.total_routes,
            "totalSources": self.total_sources,
            "activeSources": self.active_sources,
            "changesLast7Days": self.changes_last_7_days,
            "changesLast30Days": self.changes_last_30_days,
            "recentChanges": self.recent_changes,
            "sourceHealth": self.source_health,
            "routeStatistics": self.route_statistics
        }


async def get_dashboard_stats(session: AsyncSession) -> DashboardStats:
    """
    Get dashboard statistics aggregated from repositories.
    
    Args:
        session: Database session
        
    Returns:
        DashboardStats with all aggregated statistics
    """
    # Initialize repositories
    route_repo = RouteSubscriptionRepository(session)
    source_repo = SourceRepository(session)
    change_repo = PolicyChangeRepository(session)
    
    # Get total active route subscriptions (optimized: use count query)
    from api.models.db.route_subscription import RouteSubscription
    active_routes_count = await session.execute(
        select(func.count()).select_from(RouteSubscription)
        .where(RouteSubscription.is_active == True)
    )
    total_routes = active_routes_count.scalar() or 0
    
    # Get total and active sources (optimized: use count queries)
    all_sources_count = await session.execute(
        select(func.count()).select_from(Source)
    )
    total_sources = all_sources_count.scalar() or 0
    
    active_sources_count = await session.execute(
        select(func.count()).select_from(Source)
        .where(Source.is_active == True)
    )
    active_sources = active_sources_count.scalar() or 0
    
    # Get all sources for health check (we need the full objects for health calculation)
    all_sources = await source_repo.list_all()
    
    # Calculate date ranges
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # Get changes in last 7 and 30 days (optimized: use count queries)
    changes_7_days_count = await session.execute(
        select(func.count()).select_from(PolicyChange)
        .where(
            and_(
                PolicyChange.detected_at >= seven_days_ago,
                PolicyChange.detected_at <= now
            )
        )
    )
    changes_last_7_days = changes_7_days_count.scalar() or 0
    
    changes_30_days_count = await session.execute(
        select(func.count()).select_from(PolicyChange)
        .where(
            and_(
                PolicyChange.detected_at >= thirty_days_ago,
                PolicyChange.detected_at <= now
            )
        )
    )
    changes_last_30_days = changes_30_days_count.scalar() or 0
    
    # Get recent changes (last 10) with source information
    recent_changes_list = await _get_recent_changes_with_source_info(session, limit=10)
    
    # Get source health information
    source_health_list = await _get_source_health(session, all_sources)
    
    # Get route statistics
    route_statistics_list = await _get_route_statistics(session, all_sources)
    
    return DashboardStats(
        total_routes=total_routes,
        total_sources=total_sources,
        active_sources=active_sources,
        changes_last_7_days=changes_last_7_days,
        changes_last_30_days=changes_last_30_days,
        recent_changes=recent_changes_list,
        source_health=source_health_list,
        route_statistics=route_statistics_list
    )


async def _get_recent_changes_with_source_info(
    session: AsyncSession,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get recent changes with source and route information.
    
    Optimized to use a single join query instead of N+1 queries.
    
    Args:
        session: Database session
        limit: Maximum number of changes to return
        
    Returns:
        List of change dictionaries with source info
    """
    from api.models.db.policy_change import PolicyChange
    from api.models.db.source import Source
    
    # Optimized: Join query to get changes with source info in one query
    result = await session.execute(
        select(PolicyChange, Source)
        .join(Source, PolicyChange.source_id == Source.id)
        .order_by(PolicyChange.detected_at.desc())
        .limit(limit)
    )
    rows = result.all()
    
    # Build response with source information
    recent_changes = []
    for change, source in rows:
        # Format route as "Country: VisaType"
        route_display = f"{source.country}: {source.visa_type}"
        
        recent_changes.append({
            "id": str(change.id),
            "sourceId": str(change.source_id),
            "sourceName": source.name,
            "route": route_display,
            "detectedAt": change.detected_at.isoformat() if change.detected_at else None,
            "hasDiff": bool(change.diff),
            "diffLength": change.diff_length or 0
        })
    
    return recent_changes


async def _get_source_health(
    session: AsyncSession,
    sources: List[Source]
) -> List[Dict[str, Any]]:
    """
    Get health status for all sources.
    
    Args:
        session: Database session
        sources: List of all sources
        
    Returns:
        List of source health dictionaries with status
    """
    source_health = []
    now = datetime.utcnow()
    
    for source in sources:
        # Determine status: healthy, stale, or error
        status = "healthy"
        
        # Check for errors (recent errors in last 24 hours or 3+ consecutive failures)
        has_recent_error = False
        if source.consecutive_fetch_failures >= 3:
            status = "error"
            has_recent_error = True
        elif source.last_fetch_error and source.last_checked_at:
            # Check if error was recent (within 24 hours)
            hours_since_error = (now - source.last_checked_at).total_seconds() / 3600
            if hours_since_error < 24:
                status = "error"
                has_recent_error = True
        
        # Check if stale (not checked recently beyond expected frequency)
        if not has_recent_error and source.last_checked_at:
            # Calculate expected check interval based on check_frequency
            expected_interval_hours = {
                "daily": 24,
                "weekly": 168,  # 7 days
                "custom": 24  # Default to daily for custom
            }.get(source.check_frequency, 24)
            
            # Add 1 day buffer (24 hours) as per story requirement
            max_hours = expected_interval_hours + 24
            
            hours_since_check = (now - source.last_checked_at).total_seconds() / 3600
            if hours_since_check > max_hours:
                status = "stale"
        elif not has_recent_error and not source.last_checked_at:
            # Never checked - consider stale
            status = "stale"
        
        source_health.append({
            "sourceId": str(source.id),
            "sourceName": source.name,
            "country": source.country,
            "visaType": source.visa_type,
            "lastCheckedAt": source.last_checked_at.isoformat() if source.last_checked_at else None,
            "status": status,
            "consecutiveFailures": source.consecutive_fetch_failures,
            "lastError": source.last_fetch_error
        })
    
    return source_health


async def _get_route_statistics(
    session: AsyncSession,
    sources: List[Source]
) -> List[Dict[str, Any]]:
    """
    Get statistics per route (grouped by country and visa_type).
    
    Args:
        session: Database session
        sources: List of all sources
        
    Returns:
        List of route statistics dictionaries
    """
    from collections import defaultdict
    from api.models.db.policy_change import PolicyChange
    from api.models.db.route_subscription import RouteSubscription
    
    # Group sources by route (country + visa_type)
    route_sources = defaultdict(list)
    for source in sources:
        route_key = f"{source.country}:{source.visa_type}"
        route_sources[route_key].append(source)
    
    # Get all route subscriptions to find unique routes
    route_repo = RouteSubscriptionRepository(session)
    all_routes = await route_repo.list_all()
    
    # Create route set from subscriptions
    route_set = set()
    for route in all_routes:
        route_key = f"{route.destination_country}:{route.visa_type}"
        route_set.add((route.destination_country, route.visa_type, route.origin_country))
    
    # Also add routes from sources
    for source in sources:
        if source.is_active:
            # We don't know origin country from source, so we'll use destination
            route_set.add((source.country, source.visa_type, None))
    
    # Calculate statistics for each route
    route_stats = []
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    
    for destination_country, visa_type, origin_country in route_set:
        route_key = f"{destination_country}:{visa_type}"
        
        # Count sources for this route
        route_sources_list = route_sources.get(route_key, [])
        active_sources_count = sum(1 for s in route_sources_list if s.is_active)
        total_sources_count = len(route_sources_list)
        
        # Get most recent last_checked_at
        last_check = None
        for source in route_sources_list:
            if source.last_checked_at:
                if last_check is None or source.last_checked_at > last_check:
                    last_check = source.last_checked_at
        
        # Count changes for this route (matching destination country and visa type)
        # Note: PolicyChange has source_id, and source has country and visa_type
        changes_count = 0
        if route_sources_list:
            source_ids = [s.id for s in route_sources_list]
            # Get changes count for sources in this route
            changes_result = await session.execute(
                select(func.count()).select_from(PolicyChange)
                .where(PolicyChange.source_id.in_(source_ids))
                .where(PolicyChange.detected_at >= seven_days_ago)
            )
            changes_count = changes_result.scalar() or 0
        
        # Format route display
        if origin_country:
            route_display = f"{origin_country} → {destination_country}, {visa_type}"
        else:
            route_display = f"{destination_country}, {visa_type}"
        
        route_stats.append({
            "route": route_display,
            "destinationCountry": destination_country,
            "visaType": visa_type,
            "originCountry": origin_country,
            "totalSources": total_sources_count,
            "activeSources": active_sources_count,
            "changesLast7Days": changes_count,
            "lastCheck": last_check.isoformat() if last_check else None
        })
    
    # Sort by route display name
    route_stats.sort(key=lambda x: x["route"])
    
    return route_stats

