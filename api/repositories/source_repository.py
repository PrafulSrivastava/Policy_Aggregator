"""Repository for Source model."""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from api.models.db.source import Source


class SourceRepository:
    """Repository for Source database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(self, source_data: dict) -> Source:
        """
        Create a new Source.
        
        Args:
            source_data: Dictionary with source fields
            
        Returns:
            Created Source instance
        """
        source = Source(**source_data)
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source
    
    async def get_by_id(self, source_id: uuid.UUID) -> Optional[Source]:
        """
        Get Source by ID.
        
        Args:
            source_id: Source UUID
            
        Returns:
            Source instance or None if not found
        """
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        return result.scalar_one_or_none()
    
    async def list_all(self) -> List[Source]:
        """
        List all Sources.
        
        Returns:
            List of all Source instances
        """
        result = await self.session.execute(select(Source).order_by(Source.created_at.desc()))
        return list(result.scalars().all())
    
    async def list_active(self) -> List[Source]:
        """
        List all active Sources.
        
        Returns:
            List of active Source instances
        """
        result = await self.session.execute(
            select(Source)
            .where(Source.is_active == True)
            .order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update(self, source_id: uuid.UUID, update_data: dict) -> Source:
        """
        Update a Source.
        
        Args:
            source_id: Source UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated Source instance
            
        Raises:
            ValueError: If source not found
        """
        source = await self.get_by_id(source_id)
        if not source:
            raise ValueError(f"Source with id {source_id} not found")
        
        for key, value in update_data.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        await self.session.commit()
        await self.session.refresh(source)
        return source
    
    async def delete(self, source_id: uuid.UUID) -> bool:
        """
        Delete a Source.
        
        Args:
            source_id: Source UUID
            
        Returns:
            True if deleted, False if not found
        """
        source = await self.get_by_id(source_id)
        if not source:
            return False
        
        await self.session.delete(source)
        await self.session.commit()
        return True
    
    async def get_by_country_visa(self, country: str, visa_type: str) -> List[Source]:
        """
        Get Sources by country and visa type.
        
        Args:
            country: Country code (2 characters)
            visa_type: Visa type string
            
        Returns:
            List of matching Source instances
        """
        result = await self.session.execute(
            select(Source)
            .where(Source.country == country.upper())
            .where(Source.visa_type == visa_type)
            .order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_active_by_country_visa(self, country: str, visa_type: str) -> List[Source]:
        """
        Get active Sources by country and visa type.
        
        Args:
            country: Country code (2 characters)
            visa_type: Visa type string
            
        Returns:
            List of matching active Source instances
        """
        result = await self.session.execute(
            select(Source)
            .where(Source.country == country.upper())
            .where(Source.visa_type == visa_type)
            .where(Source.is_active == True)
            .order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        country: Optional[str] = None,
        visa_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Source], int]:
        """
        List Sources with pagination and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            country: Filter by country code (optional)
            visa_type: Filter by visa type (optional)
            is_active: Filter by active status (optional)
            
        Returns:
            Tuple of (list of Source instances, total count)
        """
        # Build query with filters
        query = select(Source)
        conditions = []
        
        if country:
            conditions.append(Source.country == country.upper())
        if visa_type:
            conditions.append(Source.visa_type == visa_type)
        if is_active is not None:
            conditions.append(Source.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(Source)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Source.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        return list(result.scalars().all()), total
    
    async def exists(
        self,
        url: str,
        country: str,
        visa_type: str
    ) -> bool:
        """
        Check if a Source exists with the given URL, country, and visa_type.
        
        Args:
            url: Source URL
            country: Country code (2 characters)
            visa_type: Visa type string
            
        Returns:
            True if source exists, False otherwise
        """
        result = await self.session.execute(
            select(Source)
            .where(Source.url == url)
            .where(Source.country == country.upper())
            .where(Source.visa_type == visa_type)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

