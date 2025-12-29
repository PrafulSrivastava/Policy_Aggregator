"""EmailAlert database model."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.database import Base


class EmailAlert(Base):
    """EmailAlert model representing an email alert sent for a policy change."""
    
    __tablename__ = "email_alerts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    
    # Foreign keys
    policy_change_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policy_changes.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to PolicyChange"
    )
    route_subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("route_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to RouteSubscription"
    )
    
    # Email delivery information
    sent_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when email was sent"
    )
    email_provider = Column(
        String(50),
        nullable=False,
        default="resend",
        comment="Email service provider (e.g., 'resend')"
    )
    email_provider_id = Column(
        String(255),
        nullable=True,
        comment="Provider's message ID for tracking"
    )
    status = Column(
        String(20),
        nullable=False,
        default="sent",
        comment="Delivery status: 'sent', 'failed', or 'bounced'"
    )
    error_message = Column(
        String,
        nullable=True,
        comment="Error details if sending failed"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When alert record was created"
    )
    
    # Relationships
    policy_change = relationship("PolicyChange", back_populates="email_alerts")
    route_subscription = relationship("RouteSubscription", back_populates="email_alerts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('sent', 'failed', 'bounced')",
            name="email_alerts_status_check"
        ),
        # Indexes
        Index("idx_email_alerts_policy_change_id", "policy_change_id"),
        Index("idx_email_alerts_route_subscription_id", "route_subscription_id"),
        Index("idx_email_alerts_sent_at", "sent_at", postgresql_ops={"sent_at": "DESC"}),
        Index("idx_email_alerts_status", "status"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<EmailAlert(id={self.id}, policy_change_id={self.policy_change_id}, "
            f"route_subscription_id={self.route_subscription_id}, status={self.status})>"
        )

