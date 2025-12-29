"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from api.database import Base, init_db, get_db
from api.config import Settings


# Test database URL (use in-memory SQLite for unit tests, or test PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Uses in-memory SQLite for fast unit tests.
    For integration tests, use a test PostgreSQL database.
    """
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def sample_source_data():
    """Sample source data for testing."""
    return {
        "country": "DE",
        "visa_type": "Student",
        "url": "https://example.com/student-visa",
        "name": "Germany Student Visa",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {}
    }


@pytest.fixture
def sample_policy_version_data(sample_source_data):
    """Sample policy version data for testing."""
    return {
        "source_id": None,  # Will be set in test
        "content_hash": "a" * 64,  # 64 character hash
        "raw_text": "Sample policy text",
        "fetched_at": "2025-01-27T00:00:00Z",
        "normalized_at": "2025-01-27T00:00:00Z",
        "content_length": 18,
        "fetch_duration": 100
    }


@pytest.fixture
def sample_route_subscription_data():
    """Sample route subscription data for testing."""
    return {
        "origin_country": "IN",
        "destination_country": "DE",
        "visa_type": "Student",
        "email": "test@example.com",
        "is_active": True
    }



