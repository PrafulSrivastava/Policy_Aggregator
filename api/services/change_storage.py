"""Service for storing PolicyChange records when changes are detected."""

import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.db.policy_change import PolicyChange
from api.repositories.policy_change_repository import PolicyChangeRepository

logger = logging.getLogger(__name__)


async def create_policy_change(
    session: AsyncSession,
    source_id: uuid.UUID,
    old_version_id: Optional[uuid.UUID],
    new_version_id: uuid.UUID,
    old_hash: str,
    new_hash: str,
    diff: str,
    detected_at: datetime
) -> PolicyChange:
    """
    Create a PolicyChange record when a change is detected.
    
    This function:
    1. Validates all required fields
    2. Calculates diff_length from diff text
    3. Creates immutable PolicyChange record
    4. Links to both old and new PolicyVersions via foreign keys
    5. Ensures immutability (never updates existing PolicyChange)
    
    Args:
        session: Database session
        source_id: Source UUID
        old_version_id: Previous PolicyVersion UUID (nullable for first fetch edge case)
        new_version_id: New PolicyVersion UUID
        old_hash: SHA256 hash of previous version (64 hex characters)
        new_hash: SHA256 hash of new version (64 hex characters)
        diff: Text diff showing what changed (unified diff format)
        detected_at: Timestamp when change was detected
    
    Returns:
        Created PolicyChange instance
    
    Raises:
        ValueError: If required fields are invalid
    """
    # Validate required fields
    if not source_id:
        raise ValueError("source_id cannot be None")
    if not new_version_id:
        raise ValueError("new_version_id cannot be None")
    if not old_hash or len(old_hash) != 64:
        raise ValueError(f"old_hash must be 64 characters, got {len(old_hash) if old_hash else 0}")
    if not new_hash or len(new_hash) != 64:
        raise ValueError(f"new_hash must be 64 characters, got {len(new_hash) if new_hash else 0}")
    if old_hash == new_hash:
        raise ValueError("old_hash and new_hash must be different")
    if not diff:
        raise ValueError("diff cannot be empty")
    if not detected_at:
        raise ValueError("detected_at cannot be None")
    
    # Normalize hashes to lowercase for consistency
    old_hash = old_hash.lower()
    new_hash = new_hash.lower()
    
    # Calculate diff_length
    diff_length = len(diff)
    
    logger.debug(
        f"Creating PolicyChange for source {source_id}: "
        f"{old_hash[:8]}... → {new_hash[:8]}... (diff: {diff_length} bytes)"
    )
    
    # Prepare change data
    change_data = {
        'source_id': source_id,
        'old_hash': old_hash,
        'new_hash': new_hash,
        'diff': diff,
        'detected_at': detected_at,
        'old_version_id': old_version_id,
        'new_version_id': new_version_id,
        'diff_length': diff_length
    }
    
    # Create PolicyChange using repository (ensures immutability - no update method)
    repo = PolicyChangeRepository(session)
    policy_change = await repo.create(change_data)
    
    logger.info(
        f"Created PolicyChange {policy_change.id} for source {source_id} "
        f"detected at {detected_at} (diff: {diff_length} bytes)"
    )
    
    return policy_change

