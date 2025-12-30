"""Pydantic schemas for RouteSubscription model."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr


class RouteSubscriptionBase(BaseModel):
    """Base schema for RouteSubscription."""
    origin_country: str = Field(..., min_length=2, max_length=2, description="Origin country code (2 characters)")
    destination_country: str = Field(..., min_length=2, max_length=2, description="Destination country code (2 characters)")
    visa_type: str = Field(..., max_length=50, description="Type of visa (e.g., 'Student', 'Work')")
    email: EmailStr = Field(..., description="Email address to send alerts to")
    is_active: bool = Field(default=True, description="Whether subscription is active")
    
    @field_validator('origin_country', 'destination_country')
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate country code is 2 uppercase characters."""
        if len(v) != 2:
            raise ValueError("Country code must be exactly 2 characters")
        return v.upper()


class RouteSubscriptionCreate(RouteSubscriptionBase):
    """Schema for creating a RouteSubscription."""
    pass


class RouteSubscriptionUpdate(BaseModel):
    """Schema for updating a RouteSubscription."""
    origin_country: Optional[str] = Field(None, min_length=2, max_length=2)
    destination_country: Optional[str] = Field(None, min_length=2, max_length=2)
    visa_type: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    
    @field_validator('origin_country', 'destination_country')
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate country code is 2 uppercase characters."""
        if v is not None and len(v) != 2:
            raise ValueError("Country code must be exactly 2 characters")
        return v.upper() if v else None


class RouteSubscriptionResponse(RouteSubscriptionBase):
    """Schema for RouteSubscription response."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True




