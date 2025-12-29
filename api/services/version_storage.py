"""Service for storing policy versions with idempotency and immutability guarantees."""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.db.policy_version import PolicyVersion
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.utils.hashing import generate_hash
from api.services.change_detector import detect_change
from api.services.change_storage import create_policy_change

logger = logging.getLogger(__name__)


async def store_policy_version(
    session: AsyncSession,
    source_id: uuid.UUID,
    normalized_text: str,
    fetched_at: datetime,
    fetch_metadata: Optional[Dict[str, Any]] = None
) -> PolicyVersion:
    """
    Store a policy version with idempotency check.
    
    This function:
    1. Generates SHA256 hash of normalized content
    2. Checks if hash already exists for this source (idempotency)
    3. Returns existing version if found (no duplicate created)
    4. Creates new PolicyVersion if hash is new
    5. Ensures immutability (never updates existing versions)
    
    Args:
        session: Database session
        source_id: Source UUID
        normalized_text: Normalized text content (after normalization pipeline)
        fetched_at: Timestamp when content was fetched
        fetch_metadata: Optional metadata from fetch operation (for fetch_duration, etc.)
    
    Returns:
        PolicyVersion instance (either existing or newly created)
    
    Raises:
        ValueError: If normalized_text is empty or invalid
    """
    if not normalized_text or not normalized_text.strip():
        raise ValueError("Normalized text cannot be empty")
    
    # Generate SHA256 hash of normalized content
    content_hash = generate_hash(normalized_text)
    
    # Ensure hash is lowercase for consistency
    content_hash = content_hash.lower()
    
    logger.debug(f"Generated hash for source {source_id}: {content_hash[:8]}...")
    
    # Check if version with this hash already exists for this source (idempotency)
    repo = PolicyVersionRepository(session)
    existing_version = await repo.exists_by_hash(source_id, content_hash)
    
    if existing_version:
        # Hash exists - return existing version (idempotent behavior)
        logger.info(
            f"PolicyVersion with hash {content_hash[:8]}... already exists for source {source_id}. "
            "Returning existing version (idempotent)."
        )
        # Get the existing version
        version = await repo.get_by_hash(content_hash)
        if version and version.source_id == source_id:
            return version
        # If hash exists but for different source, still create new version
        # (same content, different source is valid)
    
    # Hash is new for this source - create new PolicyVersion
    normalized_at = datetime.utcnow()
    content_length = len(normalized_text)
    
    # Extract fetch_duration from metadata if available
    fetch_duration = 0
    if fetch_metadata:
        fetch_duration = fetch_metadata.get('fetch_duration', 0)
        # Ensure it's an integer
        if not isinstance(fetch_duration, int):
            try:
                fetch_duration = int(fetch_duration)
            except (ValueError, TypeError):
                fetch_duration = 0
    
    version_data = {
        'source_id': source_id,
        'content_hash': content_hash,
        'raw_text': normalized_text,
        'fetched_at': fetched_at,
        'normalized_at': normalized_at,
        'content_length': content_length,
        'fetch_duration': fetch_duration
    }
    
    # Create new PolicyVersion (immutable - never updates existing)
    version = await repo.create(version_data)
    
    logger.info(
        f"Created new PolicyVersion {version.id} for source {source_id} "
        f"with hash {content_hash[:8]}... (length: {content_length} chars)"
    )
    
    # Call change detection after storing PolicyVersion
    try:
        change_result = await detect_change(
            session=session,
            source_id=source_id,
            new_hash=content_hash,
            new_content=normalized_text,
            new_version_id=version.id
        )
        
        # If change detected, create PolicyChange record
        if change_result.change_detected and change_result.diff:
            try:
                from datetime import datetime
                await create_policy_change(
                    session=session,
                    source_id=source_id,
                    old_version_id=change_result.old_version_id,
                    new_version_id=change_result.new_version_id,
                    old_hash=change_result.old_hash,
                    new_hash=change_result.new_hash,
                    diff=change_result.diff,
                    detected_at=datetime.utcnow()
                )
            except Exception as e:
                # Handle PolicyChange creation errors gracefully - don't fail version storage
                logger.warning(
                    f"PolicyChange creation failed for source {source_id} version {version.id}: {e}. "
                    "Version was stored and change was detected, but PolicyChange record creation failed."
                )
    except Exception as e:
        # Handle change detection errors gracefully - don't fail version storage
        logger.warning(
            f"Change detection failed for source {source_id} version {version.id}: {e}. "
            "Version was stored successfully."
        )
    
    return version


async def get_latest_policy_version(
    session: AsyncSession,
    source_id: uuid.UUID
) -> Optional[PolicyVersion]:
    """
    Get the latest PolicyVersion for a source.
    
    Args:
        session: Database session
        source_id: Source UUID
    
    Returns:
        Latest PolicyVersion or None if no versions exist
    """
    repo = PolicyVersionRepository(session)
    return await repo.get_latest_by_source_id(source_id)


async def get_policy_version_by_hash(
    session: AsyncSession,
    content_hash: str
) -> Optional[PolicyVersion]:
    """
    Get PolicyVersion by content hash.
    
    Args:
        session: Database session
        content_hash: SHA256 hash (64 hex characters)
    
    Returns:
        PolicyVersion or None if not found
    """
    repo = PolicyVersionRepository(session)
    return await repo.get_by_hash(content_hash)

