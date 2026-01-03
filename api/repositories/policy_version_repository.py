"""Repository for PolicyVersion model."""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from api.models.db.policy_version import PolicyVersion


class PolicyVersionRepository:
    """Repository for PolicyVersion database operations.
    
    Note: PolicyVersion records are immutable - no update method provided.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(self, version_data: dict) -> PolicyVersion:
        """
        Create a new PolicyVersion.
        
        Args:
            version_data: Dictionary with version fields
            
        Returns:
            Created PolicyVersion instance
        """
        version = PolicyVersion(**version_data)
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version
    
    async def get_by_id(self, version_id: uuid.UUID) -> Optional[PolicyVersion]:
        """
        Get PolicyVersion by ID.
        
        Args:
            version_id: PolicyVersion UUID
            
        Returns:
            PolicyVersion instance or None if not found
        """
        result = await self.session.execute(
            select(PolicyVersion).where(PolicyVersion.id == version_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_source_id(self, source_id: uuid.UUID) -> List[PolicyVersion]:
        """
        Get all PolicyVersions for a source, ordered by fetched_at descending.
        
        Args:
            source_id: Source UUID
            
        Returns:
            List of PolicyVersion instances for the source
        """
        result = await self.session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.source_id == source_id)
            .order_by(desc(PolicyVersion.fetched_at))
        )
        return list(result.scalars().all())
    
    async def get_latest_by_source_id(self, source_id: uuid.UUID) -> Optional[PolicyVersion]:
        """
        Get the latest PolicyVersion for a source.
        
        Args:
            source_id: Source UUID
            
        Returns:
            Latest PolicyVersion instance or None if no versions exist
        """
        result = await self.session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.source_id == source_id)
            .order_by(desc(PolicyVersion.fetched_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_hash(self, content_hash: str) -> Optional[PolicyVersion]:
        """
        Get PolicyVersion by content hash.
        
        Args:
            content_hash: SHA256 hash (64 hex characters)
            
        Returns:
            PolicyVersion instance or None if not found
        """
        result = await self.session.execute(
            select(PolicyVersion).where(PolicyVersion.content_hash == content_hash.lower())
        )
        return result.scalar_one_or_none()
    
    async def exists_by_hash(self, source_id: uuid.UUID, content_hash: str) -> bool:
        """
        Check if a PolicyVersion with the given hash exists for a source.
        Useful for idempotency checks.
        
        Args:
            source_id: Source UUID
            content_hash: SHA256 hash (64 hex characters)
            
        Returns:
            True if version exists, False otherwise
        """
        result = await self.session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.source_id == source_id)
            .where(PolicyVersion.content_hash == content_hash.lower())
            .limit(1)
        )
        return result.scalar_one_or_none() is not None





