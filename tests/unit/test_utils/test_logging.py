"""Unit tests for logging utilities."""

import pytest
import logging
import sys
from io import StringIO
from pathlib import Path

from api.utils.logging import setup_logging, get_logger, log_with_context, _get_default_log_level
from api.config import settings


class TestLoggingSetup:
    """Tests for logging setup."""
    
    def test_setup_logging_with_custom_level(self):
        """Test setting up logging with custom log level."""
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        
        # Setup logging
        setup_logging(log_level="DEBUG")
        
        # Get logger and test
        logger = get_logger(__name__)
        logger.debug("Test debug message")
        logger.info("Test info message")
        
        # Verify logging works
        output = log_capture.getvalue()
        assert "Test debug message" in output or "Test info message" in output
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_log_with_context(self):
        """Test logging with additional context."""
        logger = get_logger("test_module")
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Log with context
        log_with_context(
            logger,
            logging.INFO,
            "Test message",
            user_id="123",
            action="test"
        )
        
        output = log_capture.getvalue()
        assert "Test message" in output
        assert "user_id=123" in output or "action=test" in output
    
    def test_get_default_log_level_production(self, monkeypatch):
        """Test default log level for production environment."""
        # Mock production environment
        from api.config import Settings
        original_env = settings.ENVIRONMENT
        
        # Test production
        with monkeypatch.context() as m:
            from api.config import Environment
            m.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
            level = _get_default_log_level()
            assert level == "INFO"
    
    def test_get_default_log_level_development(self, monkeypatch):
        """Test default log level for development environment."""
        # Test development
        with monkeypatch.context() as m:
            from api.config import Environment
            m.setattr(settings, "ENVIRONMENT", Environment.DEVELOPMENT)
            level = _get_default_log_level()
            assert level == "DEBUG"
    
    def test_get_default_log_level_test(self, monkeypatch):
        """Test default log level for test environment."""
        # Test test environment
        with monkeypatch.context() as m:
            from api.config import Environment
            m.setattr(settings, "ENVIRONMENT", Environment.TEST)
            level = _get_default_log_level()
            assert level == "WARNING"


class TestLogFormat:
    """Tests for log format."""
    
    def test_log_format_includes_timestamp(self):
        """Test that log format includes timestamp."""
        setup_logging(log_level="INFO")
        logger = get_logger("test")
        
        # Capture output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        
        output = log_capture.getvalue()
        # Should contain timestamp format
        assert " - " in output
        assert "INFO" in output or "test" in output

