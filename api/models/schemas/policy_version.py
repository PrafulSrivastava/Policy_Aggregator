"""Pydantic schemas for PolicyVersion model."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class PolicyVersionCreate(BaseModel):
    """Schema for creating a PolicyVersion."""
    source_id: uuid.UUID = Field(..., description="Foreign key to Source")
    content_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash (64 hex characters)")
    raw_text: str = Field(..., description="Full text content after normalization")
    fetched_at: datetime = Field(..., description="Timestamp when content was fetched")
    normalized_at: datetime = Field(..., description="Timestamp when normalization was applied")
    content_length: int = Field(..., ge=0, description="Character count of raw text")
    fetch_duration: int = Field(..., ge=0, description="Time taken to fetch in milliseconds")
    
    @field_validator('content_hash')
    @classmethod
    def validate_hash_length(cls, v: str) -> str:
        """Validate hash is exactly 64 hex characters."""
        if len(v) != 64:
            raise ValueError("Content hash must be exactly 64 characters")
        if not all(c in '0123456789abcdefABCDEF' for c in v):
            raise ValueError("Content hash must contain only hexadecimal characters")
        return v.lower()


class PolicyVersionResponse(BaseModel):
    """Schema for PolicyVersion response."""
    id: uuid.UUID
    source_id: uuid.UUID
    content_hash: str
    raw_text: str
    fetched_at: datetime
    normalized_at: datetime
    content_length: int
    fetch_duration: int
    created_at: datetime
    
    class Config:
        from_attributes = True



