"""Health check endpoint."""

import logging
from datetime import datetime
from fastapi import APIRouter, status
from sqlalchemy import text

from api.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with application status, database status, and timestamp
    """
    # Check database connection
    database_status = "disconnected"
    try:
        if engine is not None:
            # Try to execute a simple query to check connection
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
            database_status = "connected"
        else:
            database_status = "disconnected"
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}")
        database_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": database_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

