"""RouteSubscription database model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, CheckConstraint, UniqueConstraint, Index, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.database import Base


# Event listener to conditionally apply PostgreSQL-specific constraints
@event.listens_for(Base.metadata, "before_create")
def receive_before_create(target, connection, **kw):
    """Conditionally remove PostgreSQL-specific constraints for SQLite compatibility."""
    dialect = connection.dialect.name
    if dialect == 'sqlite':
        # For SQLite, remove PostgreSQL-specific constraints
        # Validation is handled by Pydantic in the schema layer (EmailStr, length checks, etc.)
        for table in target.tables.values():
            constraints_to_remove = []
            for constraint in list(table.constraints):
                if isinstance(constraint, CheckConstraint):
                    constraint_text = str(constraint.sqltext)
                    # Remove regex constraints (~* operator) - validation done by Pydantic EmailStr
                    if '~*' in constraint_text:
                        constraints_to_remove.append(constraint)
                    # Remove char_length constraints - validation done by Pydantic
                    elif 'char_length' in constraint_text:
                        constraints_to_remove.append(constraint)
            # Remove constraints
            for constraint in constraints_to_remove:
                table.constraints.remove(constraint)


class RouteSubscription(Base):
    """RouteSubscription model representing a user's subscription to monitor a specific route."""
    
    __tablename__ = "route_subscriptions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    
    # Route definition
    origin_country = Column(
        String(2),
        nullable=False,
        comment="Origin country code (e.g., 'IN' for India)"
    )
    destination_country = Column(
        String(2),
        nullable=False,
        comment="Destination country code (e.g., 'DE' for Germany)"
    )
    visa_type = Column(
        String(50),
        nullable=False,
        comment="Type of visa (e.g., 'Student', 'Work')"
    )
    
    # Subscription details
    email = Column(
        String(255),
        nullable=False,
        comment="Email address to send alerts to"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether subscription is active"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When subscription was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        comment="When subscription was last modified"
    )
    
    # Relationships
    email_alerts = relationship(
        "EmailAlert",
        back_populates="route_subscription",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    # Note: Email validation is handled by Pydantic (EmailStr) in the schema layer
    # Database constraint only for PostgreSQL (SQLite doesn't support regex)
    __table_args__ = (
        UniqueConstraint(
            "origin_country", "destination_country", "visa_type", "email",
            name="route_subscriptions_unique"
        ),
        # PostgreSQL-only email format check (SQLite will skip this)
        # Email format is validated by Pydantic EmailStr in the schema layer
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="route_subscriptions_email_format_check"
        ),
        # Indexes
        Index("idx_route_subscriptions_destination_visa", "destination_country", "visa_type"),
        Index("idx_route_subscriptions_is_active", "is_active"),
        Index("idx_route_subscriptions_origin_destination_visa", "origin_country", "destination_country", "visa_type"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<RouteSubscription(id={self.id}, "
            f"origin={self.origin_country}, destination={self.destination_country}, "
            f"visa_type={self.visa_type}, email={self.email})>"
        )

