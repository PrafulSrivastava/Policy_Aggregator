"""Database models package."""

from api.database import Base

# Import all models so they're registered with Base.metadata
from api.models.db.source import Source
from api.models.db.policy_version import PolicyVersion
from api.models.db.policy_change import PolicyChange
from api.models.db.route_subscription import RouteSubscription
from api.models.db.email_alert import EmailAlert
from api.models.db.user import User

__all__ = [
    "Base",
    "Source",
    "PolicyVersion",
    "PolicyChange",
    "RouteSubscription",
    "EmailAlert",
    "User",
]

