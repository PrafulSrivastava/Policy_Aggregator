"""Test fixtures for alert system testing."""

import uuid
from datetime import datetime
from typing import Dict, Optional

from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.policy_version_repository import PolicyVersionRepository
from sqlalchemy.ext.asyncio import AsyncSession


async def create_test_source(
    session: AsyncSession,
    country: str = "DE",
    visa_type: str = "Student",
    url: Optional[str] = None,
    name: Optional[str] = None,
    fetch_type: str = "html",
    check_frequency: str = "daily",
    is_active: bool = True
) -> Dict:
    """
    Create a test source.
    
    Args:
        session: Database session
        country: Country code (default: "DE")
        visa_type: Visa type (default: "Student")
        url: Source URL (default: auto-generated)
        name: Source name (default: auto-generated)
        fetch_type: Fetch type (default: "html")
        check_frequency: Check frequency (default: "daily")
        is_active: Whether source is active (default: True)
        
    Returns:
        Created Source instance
    """
    source_repo = SourceRepository(session)
    
    source_data = {
        "country": country,
        "visa_type": visa_type,
        "url": url or f"https://example.com/{country.lower()}-{visa_type.lower()}-visa",
        "name": name or f"{country} {visa_type} Visa",
        "fetch_type": fetch_type,
        "check_frequency": check_frequency,
        "is_active": is_active,
        "metadata": {}
    }
    
    source = await source_repo.create(source_data)
    return source


async def create_test_route(
    session: AsyncSession,
    origin_country: str = "IN",
    destination_country: str = "DE",
    visa_type: str = "Student",
    email: str = "test@example.com",
    is_active: bool = True
) -> Dict:
    """
    Create a test route subscription.
    
    Args:
        session: Database session
        origin_country: Origin country code (default: "IN")
        destination_country: Destination country code (default: "DE")
        visa_type: Visa type (default: "Student")
        email: Email address (default: "test@example.com")
        is_active: Whether route is active (default: True)
        
    Returns:
        Created RouteSubscription instance
    """
    route_repo = RouteSubscriptionRepository(session)
    
    route_data = {
        "origin_country": origin_country,
        "destination_country": destination_country,
        "visa_type": visa_type,
        "email": email,
        "is_active": is_active
    }
    
    route = await route_repo.create(route_data)
    return route


async def create_test_policy_change(
    session: AsyncSession,
    source_id: uuid.UUID,
    old_hash: Optional[str] = None,
    new_hash: Optional[str] = None,
    diff: Optional[str] = None,
    new_version_id: Optional[uuid.UUID] = None,
    old_version_id: Optional[uuid.UUID] = None
) -> Dict:
    """
    Create a test policy change.
    
    Args:
        session: Database session
        source_id: Source UUID
        old_hash: Old content hash (default: auto-generated)
        new_hash: New content hash (default: auto-generated)
        diff: Diff text (default: auto-generated)
        new_version_id: New PolicyVersion ID (optional)
        old_version_id: Old PolicyVersion ID (optional)
        
    Returns:
        Created PolicyChange instance
    """
    change_repo = PolicyChangeRepository(session)
    
    old_hash = old_hash or ("a" * 64)
    new_hash = new_hash or ("b" * 64)
    diff = diff or "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2"
    
    change_data = {
        "source_id": source_id,
        "old_hash": old_hash,
        "new_hash": new_hash,
        "diff": diff,
        "detected_at": datetime.utcnow(),
        "new_version_id": new_version_id,
        "old_version_id": old_version_id,
        "diff_length": len(diff)
    }
    
    policy_change = await change_repo.create(change_data)
    return policy_change


async def create_test_policy_version(
    session: AsyncSession,
    source_id: uuid.UUID,
    content_hash: Optional[str] = None,
    raw_text: Optional[str] = None
) -> Dict:
    """
    Create a test policy version.
    
    Args:
        session: Database session
        source_id: Source UUID
        content_hash: Content hash (default: auto-generated)
        raw_text: Raw text content (default: auto-generated)
        
    Returns:
        Created PolicyVersion instance
    """
    version_repo = PolicyVersionRepository(session)
    
    content_hash = content_hash or ("a" * 64)
    raw_text = raw_text or "Sample policy content for testing"
    
    version_data = {
        "source_id": source_id,
        "content_hash": content_hash,
        "raw_text": raw_text,
        "fetched_at": datetime.utcnow(),
        "normalized_at": datetime.utcnow(),
        "content_length": len(raw_text),
        "fetch_duration": 100
    }
    
    version = await version_repo.create(version_data)
    return version

