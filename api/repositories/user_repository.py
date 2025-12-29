"""Repository for User model."""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.models.db.user import User


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(self, user_data: dict) -> User:
        """
        Create a new User.
        
        Args:
            user_data: Dictionary with user fields (username, hashed_password, etc.)
            
        Returns:
            Created User instance
        """
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Get User by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get User by username.
        
        Args:
            username: Username string
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: uuid.UUID, update_data: dict) -> User:
        """
        Update a User.
        
        Args:
            user_id: User UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated User instance
            
        Raises:
            ValueError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        return user

