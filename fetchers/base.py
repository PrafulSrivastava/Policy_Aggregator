"""Base fetcher interface and common utilities for source fetchers."""

from datetime import datetime
from typing import Optional, Dict, Any, Protocol
from enum import Enum
from pydantic import BaseModel, Field


class FetchErrorType(str, Enum):
    """Standard error types for fetcher operations."""
    
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"
    AUTHENTICATION_ERROR = "authentication_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class FetchResult(BaseModel):
    """
    Result of a source fetch operation.
    
    Attributes:
        raw_text: Extracted text content from the source
        content_type: Type of content fetched ("html", "pdf", or "text")
        fetched_at: Timestamp when the fetch occurred
        metadata: Additional fetch metadata (page title, last modified, etc.)
        success: Whether the fetch operation succeeded
        error_message: Error message if the fetch failed
    """
    
    raw_text: str = Field(default="", description="Extracted text content")
    content_type: str = Field(..., description="Content type: 'html', 'pdf', or 'text'")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of fetch")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional fetch metadata")
    success: bool = Field(default=True, description="Whether fetch succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SourceFetcher(Protocol):
    """
    Protocol defining the interface for source fetcher plugins.
    
    All fetcher modules must implement a `fetch()` function that matches this signature.
    """
    
    def fetch(self, url: str, metadata: Dict[str, Any]) -> FetchResult:
        """
        Fetch content from a source URL.
        
        Args:
            url: The URL to fetch content from
            metadata: Additional metadata about the source (country, visa_type, etc.)
        
        Returns:
            FetchResult containing the fetched content or error information
        
        Note:
            Fetchers should NOT raise exceptions. Instead, return a FetchResult
            with success=False and error_message set if the fetch fails.
        """
        ...

