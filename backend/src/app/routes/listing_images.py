"""
Listing image routes.

This module defines API endpoints for listing image operations.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_not_banned
from app.core.rate_limiter import limiter
from app.models.listing_image import Image
from app.models.user import User
from app.schemas.listing_image import ImagePublic, ImageUpdate
from app.services.listing_image import ListingImageService

listing_images_router = APIRouter(
    prefix="/listings",
    tags=["Listing Images"],
)


@listing_images_router.post(
    "/{listing_id}/images/upload",
    response_model=ImagePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image file to a listing",
)
@limiter.limit("10/minute;50/hour")
async def upload_image(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    listing_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="Image file to upload")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_not_banned)],
) -> Image:
    """
    Upload an image file to a listing.

    Accepts multipart/form-data file upload. Validates file type, size, and saves
    to disk with a unique filename. Creates image record in database.

    Only the seller of the listing can upload images. Maximum 10 images per listing.
    The first image uploaded will automatically be set as the thumbnail.

    Rate limit: 10 per minute (burst), 50 per hour (sustained) to prevent storage/bandwidth abuse.

    Args:
        request: FastAPI request object (required for rate limiting)
        listing_id: ID of the listing
        file: Image file (jpg, png, webp, gif - max 5MB)
        db: Database session
        current_user: Current authenticated user

    Returns:
        ImagePublic: The created image with URL to access the uploaded file

    Raises:
        HTTPException: 404 if listing not found
        HTTPException: 403 if user is not the seller
        HTTPException: 400 if validation fails or max images exceeded
        HTTPException: 413 if file too large
        HTTPException: 415 if unsupported file type
        HTTPException: 429 if rate limit exceeded
    """
    return await ListingImageService.upload(db, listing_id, file, current_user)


@listing_images_router.patch(
    "/{listing_id}/images/{image_id}",
    response_model=ImagePublic,
    summary="Update an image",
)
@limiter.limit("10/minute;30/hour")
async def update_image(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    image_id: uuid.UUID,
    image_update: ImageUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_not_banned)],
) -> Image:
    """
    Update an existing image.

    Rate limit: 10 per minute (burst), 30 per hour (sustained).

    Only the seller of the listing can update images.

    Use cases:
    - Update image URL
    - Update alt text
    - Set/unset as thumbnail (is_thumbnail: true/false)

    When is_thumbnail is set to true:
    - This image becomes the listing's thumbnail
    - All other images automatically have is_thumbnail set to false
    - The listing's thumbnail_url is updated

    Args:
        request: FastAPI request object (required for rate limiting)
        image_id: ID of the image to update
        image_update: Fields to update (url, is_thumbnail, alt_text - all optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        ImagePublic: The updated image

    Raises:
        HTTPException: 404 if image not found
        HTTPException: 403 if user is not the seller
    """
    return ListingImageService.update(db, image_id, image_update, current_user)


@listing_images_router.delete(
    "/{listing_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image",
)
@limiter.limit("5/minute;20/hour")
async def delete_image(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    image_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_not_banned)],
) -> None:
    """
    Delete an image from a listing.

    Rate limit: 5 per minute (burst), 20 per hour (sustained).

    Only the seller of the listing can delete images.
    If the deleted image was the thumbnail, another image will be
    automatically set as the thumbnail (if any remain).

    Args:
        request: FastAPI request object (required for rate limiting)
        image_id: ID of the image to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if image not found
        HTTPException: 403 if user is not the seller
    """
    ListingImageService.delete(db, image_id, current_user)
