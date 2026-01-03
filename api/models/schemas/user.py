"""Pydantic schemas for User model and authentication."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str = Field(..., min_length=1, max_length=100, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Schema for User response."""
    id: uuid.UUID
    username: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignupRequest(BaseModel):
    """Schema for signup request."""
    email: EmailStr = Field(..., description="Email address (used as username)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")


class SignupResponse(BaseModel):
    """Schema for signup response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Created user information")
    
    class Config:
        from_attributes = True

