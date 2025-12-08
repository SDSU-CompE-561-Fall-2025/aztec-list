"""
Profile schemas.

This module contains Pydantic models for profile request/response validation.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator

# Phone number validation constants
US_PHONE_DIGITS = 10


class ContactInfo(BaseModel):
    """Schema for contact information."""

    email: EmailStr | None = None
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """
        Validate phone number format.

        Args:
            v: Phone number string or None

        Returns:
            Formatted phone number string or None

        Raises:
            ValueError: If phone number is not 10 digits
        """
        if v is None or v == "":
            return None

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", v)

        # Check if it's a valid US phone number
        if len(digits) != US_PHONE_DIGITS:
            msg = f"Phone number must be {US_PHONE_DIGITS} digits (US format)"
            raise ValueError(msg)

        # Return formatted phone number
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


class ProfileBase(BaseModel):
    """Base profile schema with common fields."""

    name: str = Field(..., min_length=1, description="Full name of the user")
    campus: str | None = Field(None, description="University or campus name")
    contact_info: ContactInfo | None = Field(None, description="Contact information (email, phone)")


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""

    profile_picture_url: str | None = Field(
        None, description="Optional profile picture URL or path"
    )


class ProfileUpdate(BaseModel):
    """Schema for updating profile fields."""

    name: str | None = Field(None, min_length=1, description="Full name of the user")
    campus: str | None = Field(None, description="University or campus name")
    contact_info: ContactInfo | None = Field(None, description="Contact information (email, phone)")
    profile_picture_url: str | None = Field(None, description="Profile picture URL or path")


class ProfilePictureUpdate(BaseModel):
    """Schema for updating profile picture URL."""

    picture_url: HttpUrl = Field(..., description="Valid HTTP/HTTPS URL of the profile picture")


class ProfilePublic(ProfileBase):
    """Schema for profile response."""

    id: uuid.UUID
    user_id: uuid.UUID
    profile_picture_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfilePictureResponse(BaseModel):
    """Schema for profile picture upload response."""

    user_id: uuid.UUID
    profile_picture_url: str
    updated_at: datetime

    model_config = {"from_attributes": True}
