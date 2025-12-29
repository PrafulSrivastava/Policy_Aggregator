"""Error handling middleware for FastAPI."""

import logging
import traceback
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from api.config import settings

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSON error response
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log validation error with request context
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception
        
    Returns:
        JSON error response
    """
    # Log full error details (including stack trace) for debugging
    logger.error(
        f"Database error on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Determine error code based on exception type
    if isinstance(exc, IntegrityError):
        error_code = "DATABASE_INTEGRITY_ERROR"
        error_message = "A database integrity constraint was violated"
    else:
        error_code = "DATABASE_ERROR"
        error_message = "A database error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": error_code,
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle general unhandled exceptions.
    
    Logs full exception details (including stack trace) but returns
    user-friendly error message. Stack traces are hidden in production.
    
    Args:
        request: FastAPI request object
        exc: Exception
        
    Returns:
        JSON error response
    """
    # Log full error details with stack trace (for debugging)
    logger.critical(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # Determine user-friendly message based on environment
    if settings.ENVIRONMENT == "development":
        # In development, include exception message
        message = f"An internal server error occurred: {str(exc)}"
    else:
        # In production, use generic message
        message = "An internal server error occurred"
    
    # Build error response
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # In development, optionally include stack trace in response
    if settings.ENVIRONMENT == "development" and settings.LOG_LEVEL.upper() == "DEBUG":
        error_response["error"]["stack_trace"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )

