"""
Listing image routes.

This module defines API endpoints for listing image operations.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.listing_image import Image
from app.models.user import User
from app.schemas.listing_image import ImageCreate, ImagePublic, ImageUpdate
from app.services.listing_image import ListingImageService

listing_images_router = APIRouter(
    prefix="/listings",
    tags=["Listing Images"],
)


@listing_images_router.get(
    "/{listing_id}/images/{image_id}",
    response_model=ImagePublic,
    summary="Get a specific image",
)
async def get_image(
    image_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Image:
    """
    Get a specific image by ID.

    Args:
        image_id: ID of the image
        db: Database session
        current_user: Current authenticated user

    Returns:
        ImagePublic: The image

    Raises:
        HTTPException: 404 if image not found
        HTTPException: 403 if user is not authorized
    """
    return ListingImageService.get_by_id(db, image_id, current_user)


@listing_images_router.post(
    "/{listing_id}/images",
    response_model=ImagePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new image to a listing",
)
async def create_image(
    listing_id: uuid.UUID,
    image: ImageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Image:
    """
    Add a new image to a listing.

    Only the seller of the listing can add images. Maximum 10 images per listing.
    If this is the first image or is_thumbnail is True, it will be set as the thumbnail.

    Args:
        listing_id: ID of the listing
        image: Image creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        ImagePublic: The created image

    Raises:
        HTTPException: 404 if listing not found
        HTTPException: 403 if user is not the seller
        HTTPException: 400 if max images exceeded
    """
    return ListingImageService.create(db, listing_id, image, current_user)


@listing_images_router.patch(
    "/{listing_id}/images/{image_id}",
    response_model=ImagePublic,
    summary="Update an image",
)
async def update_image(
    image_id: uuid.UUID,
    image_update: ImageUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Image:
    """
    Update an existing image.

    Only the seller of the listing can update images.
    If is_thumbnail is set to True, this image will become the thumbnail
    and all other images will have is_thumbnail set to False.

    Args:
        image_id: ID of the image to update
        image_update: Fields to update
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
async def delete_image(
    image_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete an image from a listing.

    Only the seller of the listing can delete images.
    If the deleted image was the thumbnail, another image will be
    automatically set as the thumbnail (if any remain).

    Args:
        image_id: ID of the image to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if image not found
        HTTPException: 403 if user is not the seller
    """
    ListingImageService.delete(db, image_id, current_user)


@listing_images_router.patch(
    "/{listing_id}/images/thumbnail",
    response_model=ImagePublic,
    summary="Set listing thumbnail",
)
async def set_thumbnail(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Image:
    """
    Set an image as the thumbnail for a listing.

    Only the seller of the listing can set the thumbnail.
    All other images will have is_thumbnail set to False.

    Args:
        listing_id: ID of the listing
        image_id: ID of the image
        db: Database session
        current_user: Current authenticated user

    Returns:
        ImagePublic: The updated thumbnail image

    Raises:
        HTTPException: 404 if listing or image not found
        HTTPException: 403 if user is not the seller
        HTTPException: 400 if image doesn't belong to the listing
    """
    return ListingImageService.set_thumbnail(db, listing_id, image_id, current_user)
