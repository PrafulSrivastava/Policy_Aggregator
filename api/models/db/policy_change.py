"""PolicyChange database model."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.database import Base


class PolicyChange(Base):
    """PolicyChange model representing a detected change between policy versions."""
    
    __tablename__ = "policy_changes"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    
    # Foreign keys
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to Source"
    )
    old_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policy_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to previous PolicyVersion"
    )
    new_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policy_versions.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Foreign key to new PolicyVersion"
    )
    
    # Change data
    old_hash = Column(
        String(64),
        nullable=False,
        comment="SHA256 hash of previous version"
    )
    new_hash = Column(
        String(64),
        nullable=False,
        comment="SHA256 hash of new version"
    )
    diff = Column(
        String,
        nullable=False,
        comment="Text diff showing what changed"
    )
    diff_length = Column(
        Integer,
        nullable=False,
        comment="Character count of diff text"
    )
    
    # Timestamps
    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when change was detected"
    )
    alert_sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when email alert was sent"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When this change record was created"
    )
    
    # Relationships
    source = relationship("Source", back_populates="policy_changes")
    old_version = relationship(
        "PolicyVersion",
        foreign_keys=[old_version_id],
        back_populates="old_version_changes"
    )
    new_version = relationship(
        "PolicyVersion",
        foreign_keys=[new_version_id],
        back_populates="new_version_changes"
    )
    email_alerts = relationship(
        "EmailAlert",
        back_populates="policy_change",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "char_length(old_hash) = 64 AND char_length(new_hash) = 64",
            name="policy_changes_hash_length_check"
        ),
        CheckConstraint(
            "old_hash != new_hash",
            name="policy_changes_hash_different_check"
        ),
        # Indexes
        Index("idx_policy_changes_source_id", "source_id"),
        Index("idx_policy_changes_detected_at", "detected_at", postgresql_ops={"detected_at": "DESC"}),
        Index("idx_policy_changes_old_hash", "old_hash"),
        Index("idx_policy_changes_new_hash", "new_hash"),
        Index("idx_policy_changes_source_detected", "source_id", "detected_at", postgresql_ops={"detected_at": "DESC"}),
    )
    
    def __repr__(self) -> str:
        return f"<PolicyChange(id={self.id}, source_id={self.source_id}, detected_at={self.detected_at})>"

