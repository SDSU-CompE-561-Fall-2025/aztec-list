"""
User schemas.

This module contains Pydantic models for user request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating user fields."""

    username: str | None = None
    email: EmailStr | None = None
    is_verified: bool | None = None


class UserPublic(UserBase):
    """Schema for public user data in API responses."""

    id: uuid.UUID
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str
