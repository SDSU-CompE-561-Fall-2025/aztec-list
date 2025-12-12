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

    @field_validator("email")
    @classmethod
    def validate_edu_email(cls, v: str | None) -> str | None:
        """Validate that email ends with .edu domain."""
        if v is not None and not v.lower().endswith(".edu"):
            msg = "Email must be from a .edu domain"
            raise ValueError(msg)
        return v


class PasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str
    new_password: str


class UserPublic(UserBase):
    """Schema for public user data in API responses."""

    id: uuid.UUID
    is_verified: bool
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPublicWithEmailStatus(UserPublic):
    """Schema for user data with email sending status."""

    verification_email_sent: bool = True


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str
    user: UserPublic
