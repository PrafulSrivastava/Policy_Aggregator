"""Source service for status calculation and source-related operations."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.models.db.source import Source
from api.repositories.source_repository import SourceRepository
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository

logger = logging.getLogger(__name__)


def get_source_status(source: Source) -> str:
    """
    Calculate source status based on check history and errors.
    
    Status values:
    - "active": Source has been checked recently and has no errors
    - "error": Source has recent errors (consecutive_fetch_failures > 0)
    - "never_checked": Source has never been checked (no PolicyVersion records)
    - "stale": Source hasn't been checked within expected frequency
    
    Args:
        source: Source database model instance
        
    Returns:
        Status string: "active", "error", "never_checked", or "stale"
    """
    # Check for errors first (highest priority)
    if source.consecutive_fetch_failures > 0:
        return "error"
    
    # Check if source has been checked
    if source.last_checked_at is None:
        return "never_checked"
    
    # Check if source is stale (beyond expected check frequency)
    if source.last_checked_at:
        expected_interval = _get_expected_interval(source.check_frequency)
        if expected_interval:
            time_since_check = datetime.utcnow() - source.last_checked_at.replace(tzinfo=None)
            if time_since_check > expected_interval:
                return "stale"
    
    # Default to active if all checks pass
    return "active"


def _get_expected_interval(check_frequency: str) -> Optional[timedelta]:
    """
    Get expected time interval for check frequency.
    
    Args:
        check_frequency: Check frequency string ("daily", "weekly", "custom")
        
    Returns:
        Timedelta for expected interval, or None if custom/unknown
    """
    if check_frequency == "daily":
        return timedelta(days=1, hours=6)  # Allow 6 hours grace period
    elif check_frequency == "weekly":
        return timedelta(days=7, hours=12)  # Allow 12 hours grace period
    else:
        # Custom frequency - no automatic staleness check
        return None


async def get_source_with_status(
    session: AsyncSession,
    source_id: Optional[str] = None,
    source: Optional[Source] = None
) -> dict:
    """
    Get source data with calculated status.
    
    Args:
        session: Database session
        source_id: Source UUID (optional if source provided)
        source: Source instance (optional if source_id provided)
        
    Returns:
        Dictionary with source data and status
    """
    if source is None and source_id:
        from uuid import UUID
        source_repo = SourceRepository(session)
        source = await source_repo.get_by_id(UUID(source_id))
    
    if not source:
        raise ValueError("Source not found")
    
    status = get_source_status(source)
    
    # Convert source to dict
    source_dict = {
        "id": str(source.id),
        "country": source.country,
        "visa_type": source.visa_type,
        "url": source.url,
        "name": source.name,
        "fetch_type": source.fetch_type,
        "check_frequency": source.check_frequency,
        "is_active": source.is_active,
        "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
        "last_change_detected_at": source.last_change_detected_at.isoformat() if source.last_change_detected_at else None,
        "status": status,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None
    }
    
    return source_dict


async def check_source_has_versions_or_changes(
    session: AsyncSession,
    source_id: str
) -> dict:
    """
    Check if source has policy versions or changes.
    
    Args:
        session: Database session
        source_id: Source UUID string
        
    Returns:
        Dictionary with has_versions and has_changes boolean flags
    """
    from uuid import UUID
    
    source_uuid = UUID(source_id)
    
    # Check for versions
    version_repo = PolicyVersionRepository(session)
    versions = await version_repo.get_by_source_id(source_uuid)
    has_versions = len(versions) > 0
    
    # Check for changes
    change_repo = PolicyChangeRepository(session)
    changes = await change_repo.get_by_source_id(source_uuid)
    has_changes = len(changes) > 0
    
    return {
        "has_versions": has_versions,
        "has_changes": has_changes,
        "version_count": len(versions),
        "change_count": len(changes)
    }

