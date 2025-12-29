"""System status service for monitoring and health checks."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from api.repositories.source_repository import SourceRepository
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.models.db.source import Source
from api.services.source import get_source_status, _get_expected_interval

logger = logging.getLogger(__name__)


def calculate_next_check_time(
    last_checked_at: Optional[datetime],
    check_frequency: str
) -> Optional[datetime]:
    """
    Calculate next expected check time based on last checked time and frequency.
    
    Args:
        last_checked_at: Last successful check timestamp
        check_frequency: Check frequency ("daily", "weekly", "custom")
        
    Returns:
        Next expected check datetime, or None if cannot be calculated
    """
    if not last_checked_at:
        return None
    
    # Handle timezone-aware datetime
    if last_checked_at.tzinfo:
        # Convert to UTC naive for calculation
        last_checked = last_checked_at.replace(tzinfo=None)
    else:
        last_checked = last_checked_at
    
    if check_frequency == "daily":
        next_check = last_checked + timedelta(days=1)
    elif check_frequency == "weekly":
        next_check = last_checked + timedelta(days=7)
    else:
        # Custom frequency - cannot calculate
        return None
    
    return next_check


async def get_system_status(session: AsyncSession) -> Dict[str, Any]:
    """
    Get comprehensive system status including all sources with health information.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary with system status data:
        {
            "sources": [source_status_dict, ...],
            "statistics": {
                "total_sources": int,
                "healthy_sources": int,
                "error_sources": int,
                "stale_sources": int,
                "never_checked_sources": int
            },
            "last_daily_job_run": Optional[str]  # ISO format timestamp or None
        }
    """
    source_repo = SourceRepository(session)
    change_repo = PolicyChangeRepository(session)
    
    # Get all sources
    all_sources = await source_repo.list_all()
    
    # Get last change for each source (for last_change_detected_at)
    sources_with_status = []
    healthy_count = 0
    error_count = 0
    stale_count = 0
    never_checked_count = 0
    
    for source in all_sources:
        # Calculate status
        status = get_source_status(source)
        
        # Map "active" to "healthy" for consistency with story requirements
        if status == "active":
            status = "healthy"
        
        # Count by status
        if status == "healthy":
            healthy_count += 1
        elif status == "error":
            error_count += 1
        elif status == "stale":
            stale_count += 1
        elif status == "never_checked":
            never_checked_count += 1
        
        # Get last change for this source
        last_change = await change_repo.get_latest_by_source_id(source.id)
        last_change_detected_at = None
        if last_change and last_change.detected_at:
            last_change_detected_at = last_change.detected_at.isoformat()
        
        # Calculate next expected check time
        next_check_time = calculate_next_check_time(
            source.last_checked_at,
            source.check_frequency
        )
        next_check_time_str = next_check_time.isoformat() if next_check_time else None
        
        # Build source status dict
        source_status = {
            "id": str(source.id),
            "name": source.name,
            "country": source.country,
            "visa_type": source.visa_type,
            "url": source.url,
            "fetch_type": source.fetch_type,
            "check_frequency": source.check_frequency,
            "is_active": source.is_active,
            "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
            "last_change_detected_at": last_change_detected_at,
            "status": status,
            "consecutive_fetch_failures": source.consecutive_fetch_failures,
            "last_fetch_error": source.last_fetch_error,
            "next_check_time": next_check_time_str
        }
        
        sources_with_status.append(source_status)
    
    # Sort sources by status priority (errors first, then stale, never_checked, healthy)
    status_priority = {
        "error": 0,
        "stale": 1,
        "never_checked": 2,
        "healthy": 3
    }
    
    sources_with_status.sort(
        key=lambda s: (
            status_priority.get(s["status"], 99),
            s["last_checked_at"] or "9999-12-31"  # Oldest first within same status
        )
    )
    
    # Get last daily job run timestamp
    # Note: For MVP, we don't have job tracking in database
    # We'll return None and this can be enhanced later
    last_daily_job_run = None
    
    return {
        "sources": sources_with_status,
        "statistics": {
            "total_sources": len(all_sources),
            "healthy_sources": healthy_count,
            "error_sources": error_count,
            "stale_sources": stale_count,
            "never_checked_sources": never_checked_count
        },
        "last_daily_job_run": last_daily_job_run
    }

