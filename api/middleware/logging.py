"""Request logging middleware for FastAPI."""

import logging
import time
from typing import Callable, Set
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Sensitive headers that should not be logged
SENSITIVE_HEADERS: Set[str] = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-auth-token",
    "password",
    "secret",
    "token"
}

# Paths that should not be logged (health checks, etc.)
EXCLUDED_PATHS: Set[str] = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json"
}

# Slow request threshold (seconds)
SLOW_REQUEST_THRESHOLD = 1.0


def _sanitize_headers(headers: dict) -> dict:
    """
    Remove sensitive headers from logging.
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        Sanitized headers dictionary
    """
    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_HEADERS):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    return sanitized


def _should_log_path(path: str) -> bool:
    """
    Check if a path should be logged.
    
    Args:
        path: Request path
        
    Returns:
        True if path should be logged, False otherwise
    """
    return path not in EXCLUDED_PATHS


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response information.
        
        Excludes sensitive data from logs and logs slow requests as warnings.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
            
        Returns:
            Response object
        """
        # Skip logging for excluded paths
        if not _should_log_path(request.url.path):
            return await call_next(request)
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        start_time = time.time()
        
        # Log incoming request (without sensitive headers)
        sanitized_headers = _sanitize_headers(dict(request.headers))
        logger.info(
            f"Request: {request.method} {request.url.path} | "
            f"Client: {client_ip} | "
            f"Query: {dict(request.query_params)}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Determine log level based on status code and duration
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            elif duration > SLOW_REQUEST_THRESHOLD:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            
            # Build log message
            log_message = (
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
            
            if duration > SLOW_REQUEST_THRESHOLD:
                log_message += f" | SLOW REQUEST (> {SLOW_REQUEST_THRESHOLD}s)"
            
            # Log response
            logger.log(
                log_level,
                log_message,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "client_ip": client_ip
                }
            )
            
            return response
            
        except Exception as e:
            # Log exception with duration
            duration = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} | "
                f"Exception: {type(e).__name__} | "
                f"Duration: {duration:.3f}s",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "client_ip": client_ip,
                    "error_type": type(e).__name__
                }
            )
            raise

