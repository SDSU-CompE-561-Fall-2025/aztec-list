"""
Profile schemas.

This module contains Pydantic models for profile request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Schema for contact information."""

    email: str | None = None
    phone: str | None = None


class ProfileBase(BaseModel):
    """Base profile schema with common fields."""

    name: str = Field(..., min_length=1, description="Full name of the user")
    campus: str | None = Field(None, description="University or campus name")
    contact_info: ContactInfo | None = Field(None, description="Contact information (email, phone)")


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""


class ProfileUpdate(BaseModel):
    """Schema for updating profile fields."""

    name: str | None = Field(None, min_length=1, description="Full name of the user")
    campus: str | None = Field(None, description="University or campus name")
    contact_info: ContactInfo | None = Field(None, description="Contact information (email, phone)")


class ProfilePublic(ProfileBase):
    """Schema for profile response."""

    id: int
    user_id: int
    profile_picture_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfilePictureResponse(BaseModel):
    """Schema for profile picture upload response."""

    user_id: int
    profile_picture_url: str
    updated_at: datetime

    model_config = {"from_attributes": True}
