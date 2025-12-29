"""Change detection service for policy content using hash comparison."""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.policy_version_repository import PolicyVersionRepository
from api.services.diff_generator import generate_diff

logger = logging.getLogger(__name__)


@dataclass
class ChangeDetectionResult:
    """Result of change detection operation."""
    change_detected: bool
    new_hash: str
    new_version_id: uuid.UUID
    old_hash: Optional[str] = None
    is_first_fetch: bool = False
    old_version_id: Optional[uuid.UUID] = None
    diff: Optional[str] = None


async def detect_change(
    session: AsyncSession,
    source_id: uuid.UUID,
    new_hash: str,
    new_content: str,
    new_version_id: uuid.UUID
) -> ChangeDetectionResult:
    """
    Detect if policy content has changed by comparing hashes.
    
    Args:
        session: Database session
        source_id: UUID of the source being checked
        new_hash: SHA256 hash of the new content (64 hex characters)
        new_content: Normalized text content (for future extensibility, not used in hash comparison)
        new_version_id: UUID of the newly stored PolicyVersion
    
    Returns:
        ChangeDetectionResult with change_detected flag and details
    
    Raises:
        ValueError: If source_id or new_hash is invalid
    """
    if not source_id:
        raise ValueError("source_id cannot be None")
    if not new_hash or len(new_hash) != 64:
        raise ValueError(f"new_hash must be 64 characters, got {len(new_hash) if new_hash else 0}")
    
    # Normalize hash to lowercase for comparison
    new_hash = new_hash.lower()
    
    # Retrieve latest PolicyVersion for source (use repository)
    # Exclude the current version to get the previous one
    repo = PolicyVersionRepository(session)
    all_versions = await repo.get_by_source_id(source_id)
    
    # Filter out the current version to get the previous one
    previous_version = None
    for version in all_versions:
        if version.id != new_version_id:
            previous_version = version
            break
    
    # Handle first fetch case (no previous version)
    if previous_version is None:
        logger.info(f"First fetch for source {source_id}")
        return ChangeDetectionResult(
            change_detected=False,
            new_hash=new_hash,
            new_version_id=new_version_id,
            is_first_fetch=True
        )
    
    # Get previous version's hash
    old_hash = previous_version.content_hash.lower()
    old_version_id = previous_version.id
    
    # Compare hashes (simple string comparison - fast and deterministic)
    if old_hash == new_hash:
        # Hashes match: no change detected
        logger.debug(f"No change detected for source {source_id}: hash {new_hash[:8]}...")
        return ChangeDetectionResult(
            change_detected=False,
            new_hash=new_hash,
            new_version_id=new_version_id,
            old_hash=old_hash,
            old_version_id=old_version_id
        )
    else:
        # Hashes differ: change detected - generate diff
        logger.info(
            f"Change detected for source {source_id}: "
            f"{old_hash[:8]}... → {new_hash[:8]}..."
        )
        
        # Retrieve new PolicyVersion text for diff generation
        # We already have previous_version, so we can use its raw_text directly
        new_version = await repo.get_by_id(new_version_id)
        
        diff_text = None
        if previous_version and new_version:
            try:
                # Generate diff comparing old and new text
                diff_text = generate_diff(
                    old_text=previous_version.raw_text,
                    new_text=new_version.raw_text,
                    context_lines=3,
                    fromfile=f"version_{previous_version.id}",
                    tofile=f"version_{new_version.id}"
                )
                logger.debug(f"Generated diff for source {source_id} ({len(diff_text)} bytes)")
            except Exception as e:
                logger.warning(
                    f"Failed to generate diff for source {source_id}: {e}. "
                    "Change detected but diff generation failed."
                )
        else:
            logger.warning(
                f"Could not retrieve version text for diff generation "
                f"(previous_version: {previous_version is not None}, new_version: {new_version is not None})"
            )
        
        return ChangeDetectionResult(
            change_detected=True,
            new_hash=new_hash,
            new_version_id=new_version_id,
            old_hash=old_hash,
            old_version_id=old_version_id,
            diff=diff_text
        )

