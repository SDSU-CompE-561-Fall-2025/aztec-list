"""
Listing image schemas.

This module defines Pydantic schemas for listing image operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, HttpUrl

if TYPE_CHECKING:
    import uuid
    from datetime import datetime


class ImageBase(BaseModel):
    """Base schema for image data."""

    url: HttpUrl = Field(..., description="URL of the image")
    is_thumbnail: bool = Field(default=False, description="Whether this is the thumbnail image")
    alt_text: str | None = Field(None, description="Alternative text for the image")


class ImageCreate(ImageBase):
    """Schema for creating a new image."""

    listing_id: uuid.UUID = Field(..., description="ID of the listing this image belongs to")


class ImageUpdate(BaseModel):
    """Schema for updating an existing image."""

    url: HttpUrl | None = Field(None, description="URL of the image")
    is_thumbnail: bool | None = Field(None, description="Whether this is the thumbnail image")
    alt_text: str | None = Field(None, description="Alternative text for the image")


class ImagePublic(ImageBase):
    """Schema for public image representation."""

    id: uuid.UUID = Field(..., description="Unique identifier for the image")
    listing_id: uuid.UUID = Field(..., description="ID of the listing this image belongs to")
    created_at: datetime = Field(..., description="Timestamp when the image was created")

    model_config = {"from_attributes": True}


class SetThumbnailRequest(BaseModel):
    """Schema for setting a listing thumbnail."""

    image_id: uuid.UUID = Field(..., description="ID of the image to set as thumbnail")
