"""Logging configuration for the application."""

import logging
import sys
import os
from typing import Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path

from api.config import settings


def _get_default_log_level() -> str:
    """
    Get default log level based on environment.
    
    Returns:
        Default log level string
    """
    if settings.ENVIRONMENT == "production":
        return "INFO"
    elif settings.ENVIRONMENT == "staging":
        return "INFO"
    elif settings.ENVIRONMENT == "test":
        return "WARNING"
    else:  # development
        return "DEBUG"


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure Python logging module with structured format.
    
    Configures:
    - Structured log format: timestamp, level, module, message
    - Environment-based default log levels
    - Stdout handler (for Railway/hosting platforms)
    - Optional file handler with rotation (development only)
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, uses LOG_LEVEL from settings or environment-based default.
    """
    # Determine log level
    if log_level:
        level_str = log_level
    elif settings.LOG_LEVEL:
        level_str = settings.LOG_LEVEL
    else:
        level_str = _get_default_log_level()
    
    # Map string level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    log_level_value = level_map.get(level_str.upper(), logging.INFO)
    
    # Create structured formatter
    # Format: timestamp - level - module - message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_value)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add stdout handler (always enabled for Railway/hosting platforms)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level_value)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)
    
    # Add file handler with rotation (development only, optional)
    if settings.ENVIRONMENT == "development":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "app.log"
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level_value)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set log level for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured - Level: {level_str}, Environment: {settings.ENVIRONMENT.value}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context
) -> None:
    """
    Log a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (logging.DEBUG, logging.INFO, etc.)
        message: Log message
        **context: Additional context fields to include in log
    """
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        full_message = f"{message} | {context_str}"
    else:
        full_message = message
    
    logger.log(level, full_message)

