"""PolicyVersion database model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.database import Base


class PolicyVersion(Base):
    """PolicyVersion model representing an immutable version of policy content."""
    
    __tablename__ = "policy_versions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    
    # Foreign key
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to Source"
    )
    
    # Content
    content_hash = Column(
        String(64),
        nullable=False,
        comment="SHA256 hash of normalized content (64 hex characters)"
    )
    raw_text = Column(
        String,
        nullable=False,
        comment="Full text content after normalization"
    )
    
    # Fetch metadata
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when content was fetched"
    )
    normalized_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when normalization was applied"
    )
    content_length = Column(
        Integer,
        nullable=False,
        comment="Character count of raw text"
    )
    fetch_duration = Column(
        Integer,
        nullable=False,
        comment="Time taken to fetch in milliseconds"
    )
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When this version was created"
    )
    
    # Relationships
    source = relationship("Source", back_populates="policy_versions")
    old_version_changes = relationship(
        "PolicyChange",
        foreign_keys="PolicyChange.old_version_id",
        back_populates="old_version"
    )
    new_version_changes = relationship(
        "PolicyChange",
        foreign_keys="PolicyChange.new_version_id",
        back_populates="new_version"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "char_length(content_hash) = 64",
            name="policy_versions_hash_length_check"
        ),
        # Indexes
        Index("idx_policy_versions_source_id", "source_id"),
        Index("idx_policy_versions_content_hash", "content_hash"),
        Index("idx_policy_versions_fetched_at", "fetched_at", postgresql_ops={"fetched_at": "DESC"}),
        Index("idx_policy_versions_source_fetched", "source_id", "fetched_at", postgresql_ops={"fetched_at": "DESC"}),
    )
    
    def __repr__(self) -> str:
        return f"<PolicyVersion(id={self.id}, source_id={self.source_id}, content_hash={self.content_hash[:8]}...)>"

