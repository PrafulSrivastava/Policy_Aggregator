"""Source database model."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import TypeDecorator

from api.database import Base


class FlexibleJSON(TypeDecorator):
    """JSON type that uses JSONB for PostgreSQL and JSON for SQLite."""
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class Source(Base):
    """Source model representing a government policy source."""
    
    __tablename__ = "sources"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    
    # Source identification
    country = Column(String(2), nullable=False, comment="ISO country code (2 characters)")
    visa_type = Column(String(50), nullable=False, comment="Type of visa (e.g., 'Student', 'Work')")
    url = Column(String, nullable=False, comment="Source URL to fetch from")
    name = Column(String(255), nullable=False, comment="Human-readable name for the source")
    
    # Fetch configuration
    fetch_type = Column(
        String(10),
        nullable=False,
        comment="How to fetch content: 'html' or 'pdf'"
    )
    check_frequency = Column(
        String(20),
        nullable=False,
        comment="How often to check: 'daily', 'weekly', or 'custom'"
    )
    
    # Status tracking
    is_active = Column(Boolean, nullable=False, default=True, comment="Whether source is currently being monitored")
    last_checked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful fetch"
    )
    last_change_detected_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last change detected"
    )
    
    # Error tracking
    consecutive_fetch_failures = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of consecutive fetch failures"
    )
    consecutive_email_failures = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of consecutive email delivery failures"
    )
    last_fetch_error = Column(
        String,
        nullable=True,
        comment="Last fetch error message"
    )
    last_email_error = Column(
        String,
        nullable=True,
        comment="Last email delivery error message"
    )
    
    # Metadata
    source_metadata = Column(
        "metadata",
        FlexibleJSON(),
        nullable=False,
        default=dict,
        server_default="'{}'::jsonb" if False else None,  # PostgreSQL only
        comment="Additional configuration (JSONB for flexibility)"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When source was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When source was last modified"
    )
    
    # Relationships
    policy_versions = relationship(
        "PolicyVersion",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    policy_changes = relationship(
        "PolicyChange",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "fetch_type IN ('html', 'pdf')",
            name="sources_fetch_type_check"
        ),
        CheckConstraint(
            "check_frequency IN ('daily', 'weekly', 'custom')",
            name="sources_check_frequency_check"
        ),
        UniqueConstraint(
            "url", "country", "visa_type",
            name="sources_url_unique"
        ),
        # Indexes
        Index("idx_sources_country_visa", "country", "visa_type"),
        Index("idx_sources_is_active", "is_active"),
        Index("idx_sources_last_checked", "last_checked_at"),
        Index("idx_sources_metadata", "metadata", postgresql_using="gin"),
    )
    
    def __repr__(self) -> str:
        return f"<Source(id={self.id}, country={self.country}, visa_type={self.visa_type}, url={self.url})>"

