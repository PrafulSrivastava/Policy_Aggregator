"""Database connection and session management for async SQLAlchemy."""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from api.config import settings

logger = logging.getLogger(__name__)

# Base class for all database models
Base = declarative_base()

# Database engine with connection pooling
engine: AsyncEngine = None
async_session_maker: async_sessionmaker[AsyncSession] = None


def get_database_url() -> str:
    """
    Get database URL, converting postgresql:// to postgresql+asyncpg:// if needed.
    
    Returns:
        Database URL with asyncpg driver
    """
    database_url = settings.DATABASE_URL
    
    # Convert postgresql:// to postgresql+asyncpg:// for async support
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not database_url.startswith("postgresql+asyncpg://"):
        raise ValueError(
            f"Invalid DATABASE_URL format. Expected postgresql:// or postgresql+asyncpg://, "
            f"got: {database_url[:20]}..."
        )
    
    return database_url


def init_db() -> None:
    """
    Initialize database connection and session factory.
    
    Configures connection pooling with:
    - pool_size: Number of connections to maintain
    - max_overflow: Additional connections allowed beyond pool_size
    - pool_timeout: Seconds to wait for connection from pool
    - pool_recycle: Seconds before recycling connection
    """
    global engine, async_session_maker
    
    database_url = get_database_url()
    
    # Connection pool configuration
    pool_kwargs = {
        "pool_size": 5,  # Number of connections to maintain
        "max_overflow": 10,  # Additional connections allowed
        "pool_timeout": 30,  # Seconds to wait for connection
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before using
    }
    
    # Use NullPool for testing (no connection pooling)
    if settings.ENVIRONMENT == "test":
        pool_kwargs = {"poolclass": NullPool}
    
    try:
        engine = create_async_engine(
            database_url,
            echo=settings.LOG_LEVEL == "DEBUG",  # Log SQL queries in debug mode
            **pool_kwargs
        )
        
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        logger.info(
            "Database connection initialized successfully",
            extra={
                "pool_size": pool_kwargs.get("pool_size", "N/A"),
                "max_overflow": pool_kwargs.get("max_overflow", "N/A"),
                "environment": settings.ENVIRONMENT.value
            }
        )
        
    except Exception as e:
        logger.critical(
            f"Failed to initialize database connection: {e}",
            exc_info=True,
            extra={
                "environment": settings.ENVIRONMENT.value,
                "database_url_prefix": database_url[:20] + "..." if len(database_url) > 20 else database_url
            }
        )
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections and dispose of engine."""
    global engine, async_session_maker
    
    if engine:
        try:
            await engine.dispose()
            engine = None
            async_session_maker = None
            logger.info("Database connections closed successfully")
        except Exception as e:
            logger.error(
                f"Error closing database connections: {e}",
                exc_info=True
            )
            raise

