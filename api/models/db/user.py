"""User database model."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from api.database import Base


class User(Base):
    """User model for authentication (single admin user for MVP)."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    
    # Authentication
    username = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="Unique username"
    )
    hashed_password = Column(
        String(255),
        nullable=True,  # Nullable for OAuth-only users
        comment="Bcrypt hashed password (nullable for OAuth users)"
    )
    google_id = Column(
        String(255),
        nullable=True,
        unique=True,
        comment="Google user ID for OAuth authentication"
    )
    auth_provider = Column(
        String(50),
        nullable=False,
        default="password",
        comment="Authentication provider: 'password' or 'google'"
    )
    
    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether user account is active"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When user was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When user was last modified"
    )
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last login"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_is_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, is_active={self.is_active})>"

