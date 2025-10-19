"""
User schemas.

This module contains Pydantic models for user request/response validation.
"""

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
    """Schema for user response."""

    username: str | None = None
    email: EmailStr | None = None
    is_verified: bool | None = None


class UserPublic(UserBase):
    id: int
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str
