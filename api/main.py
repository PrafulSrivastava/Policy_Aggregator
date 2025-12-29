"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from api.config import settings
from api.database import init_db, close_db
from api.utils.logging import setup_logging
from api.middleware.error_handler import (
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)
from api.middleware.logging import RequestLoggingMiddleware
from api.routes import health, auth
from api.routes.api import routes_router, sources_router, jobs_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting application...")
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# Initialize FastAPI application
app = FastAPI(
    title="Policy Aggregator API",
    description="Route-scoped regulatory change monitoring system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(routes_router)
app.include_router(sources_router)
app.include_router(jobs_router)


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict:
    """
    Root endpoint.
    
    Returns:
        Welcome message and API information
    """
    return {
        "message": "Policy Aggregator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

