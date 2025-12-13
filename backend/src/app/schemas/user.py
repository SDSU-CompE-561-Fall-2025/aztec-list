"""
User schemas.

This module contains Pydantic models for user request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.core.enums import UserRole


class UserBase(BaseModel):
    """Base user schema."""

    username: str
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_edu_email(cls, v: str) -> str:
        """Validate that email ends with .edu domain."""
        if not v.lower().endswith(".edu"):
            msg = "Email must be from a .edu domain"
            raise ValueError(msg)
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating user fields."""

    username: str | None = None
    email: EmailStr | None = None


class PasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str
    new_password: str


class UserPublic(BaseModel):
    """Schema for public user data in API responses."""

    id: uuid.UUID
    username: str
    is_verified: bool
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPrivate(UserPublic):
    """Schema for private user data - includes email for authenticated user's own data."""

    email: EmailStr


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str
    user: UserPrivate
