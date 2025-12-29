"""Pydantic schemas for PolicyChange model."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PolicyChangeCreate(BaseModel):
    """Schema for creating a PolicyChange."""
    source_id: uuid.UUID = Field(..., description="Foreign key to Source")
    old_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash of previous version")
    new_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash of new version")
    diff: str = Field(..., description="Text diff showing what changed")
    detected_at: datetime = Field(..., description="Timestamp when change was detected")
    old_version_id: Optional[uuid.UUID] = Field(None, description="Foreign key to previous PolicyVersion")
    new_version_id: uuid.UUID = Field(..., description="Foreign key to new PolicyVersion")
    diff_length: int = Field(..., ge=0, description="Character count of diff text")
    alert_sent_at: Optional[datetime] = Field(None, description="Timestamp when email alert was sent")
    
    @field_validator('old_hash', 'new_hash')
    @classmethod
    def validate_hash_length(cls, v: str) -> str:
        """Validate hash is exactly 64 hex characters."""
        if len(v) != 64:
            raise ValueError("Hash must be exactly 64 characters")
        if not all(c in '0123456789abcdefABCDEF' for c in v):
            raise ValueError("Hash must contain only hexadecimal characters")
        return v.lower()
    
    @field_validator('new_hash')
    @classmethod
    def validate_hashes_different(cls, v: str, info) -> str:
        """Validate that old_hash and new_hash are different."""
        if 'old_hash' in info.data and v == info.data['old_hash']:
            raise ValueError("Old hash and new hash must be different")
        return v


class PolicyChangeResponse(BaseModel):
    """Schema for PolicyChange response."""
    id: uuid.UUID
    source_id: uuid.UUID
    old_hash: str
    new_hash: str
    diff: str
    detected_at: datetime
    old_version_id: Optional[uuid.UUID]
    new_version_id: uuid.UUID
    diff_length: int
    alert_sent_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True



