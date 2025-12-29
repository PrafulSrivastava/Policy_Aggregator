"""Pydantic schemas for Source model."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl
from enum import Enum


class FetchType(str, Enum):
    """Fetch type enum."""
    HTML = "html"
    PDF = "pdf"


class CheckFrequency(str, Enum):
    """Check frequency enum."""
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class SourceBase(BaseModel):
    """Base schema for Source."""
    country: str = Field(..., min_length=2, max_length=2, description="ISO country code (2 characters)")
    visa_type: str = Field(..., max_length=50, description="Type of visa (e.g., 'Student', 'Work')")
    url: str = Field(..., description="Source URL to fetch from")
    name: str = Field(..., max_length=255, description="Human-readable name for the source")
    fetch_type: FetchType = Field(..., description="How to fetch content: 'html' or 'pdf'")
    check_frequency: CheckFrequency = Field(..., description="How often to check: 'daily', 'weekly', or 'custom'")
    is_active: bool = Field(default=True, description="Whether source is currently being monitored")
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="source_metadata", description="Additional configuration (JSONB)")
    
    @field_validator('country')
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate country code is 2 uppercase characters."""
        if len(v) != 2:
            raise ValueError("Country code must be exactly 2 characters")
        return v.upper()
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class SourceCreate(SourceBase):
    """Schema for creating a Source."""
    pass


class SourceUpdate(BaseModel):
    """Schema for updating a Source."""
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    visa_type: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = None
    name: Optional[str] = Field(None, max_length=255)
    fetch_type: Optional[FetchType] = None
    check_frequency: Optional[CheckFrequency] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="source_metadata")
    
    @field_validator('country')
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate country code is 2 uppercase characters."""
        if v is not None and len(v) != 2:
            raise ValueError("Country code must be exactly 2 characters")
        return v.upper() if v else None
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class SourceResponse(SourceBase):
    """Schema for Source response."""
    id: uuid.UUID
    last_checked_at: Optional[datetime] = None
    last_change_detected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True

