"""
Listing image routes.

This module defines API endpoints for listing image operations.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_db
from app.schemas.listing_image import ImageCreate, ImagePublic, ImageUpdate, SetThumbnailRequest
from app.services.listing_image import ListingImageService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.user import User

listing_images_router = APIRouter(prefix="/listings", tags=["listing-images"])


@listing_images_router.get(
    "/{listing_id}/images",
    response_model=list[ImagePublic],
    summary="Get all images for a listing",
)
def get_listing_images(
    listing_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user)] = None,
) -> list[ImagePublic]:
    """
    Get all images for a listing.

    Args:
        listing_id: ID of the listing
        db: Database session
        current_user: Optional current user

    Returns:
        list[ImagePublic]: List of images for the listing

    Raises:
        HTTPException: 404 if listing not found
    """
    try:
        listing_uuid = uuid.UUID(listing_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid listing ID format"
        ) from exc

    images = ListingImageService.get_by_listing(db, listing_uuid, current_user)
    return [ImagePublic.model_validate(img) for img in images]


@listing_images_router.get(
    "/{listing_id}/images/{image_id}",
    response_model=ImagePublic,
    summary="Get a specific image",
)
def get_image(
    image_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ImagePublic:
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
    try:
        image_uuid = uuid.UUID(image_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image ID format"
        ) from exc

    image = ListingImageService.get_by_id(db, image_uuid, current_user)
    return ImagePublic.model_validate(image)


@listing_images_router.post(
    "/{listing_id}/images",
    response_model=ImagePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new image to a listing",
)
def create_image(
    listing_id: str,
    image: ImageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ImagePublic:
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
        HTTPException: 400 if max images exceeded or listing_id mismatch
    """
    try:
        listing_uuid = uuid.UUID(listing_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid listing ID format"
        ) from exc

    # Verify listing_id in path matches listing_id in body
    if image.listing_id != listing_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing ID in URL does not match listing ID in request body",
        )

    created_image = ListingImageService.create(db, image, current_user)
    return ImagePublic.model_validate(created_image)


@listing_images_router.patch(
    "/{listing_id}/images/{image_id}",
    response_model=ImagePublic,
    summary="Update an image",
)
def update_image(
    image_id: str,
    image_update: ImageUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ImagePublic:
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
    try:
        image_uuid = uuid.UUID(image_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image ID format"
        ) from exc

    updated_image = ListingImageService.update(db, image_uuid, image_update, current_user)
    return ImagePublic.model_validate(updated_image)


@listing_images_router.delete(
    "/{listing_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image",
)
def delete_image(
    image_id: str,
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
    try:
        image_uuid = uuid.UUID(image_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image ID format"
        ) from exc

    ListingImageService.delete(db, image_uuid, current_user)


@listing_images_router.patch(
    "/{listing_id}/images/thumbnail",
    response_model=ImagePublic,
    summary="Set listing thumbnail",
)
def set_thumbnail(
    listing_id: str,
    request: SetThumbnailRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ImagePublic:
    """
    Set an image as the thumbnail for a listing.

    Only the seller of the listing can set the thumbnail.
    All other images will have is_thumbnail set to False.

    Args:
        listing_id: ID of the listing
        request: Request containing image_id to set as thumbnail
        db: Database session
        current_user: Current authenticated user

    Returns:
        ImagePublic: The updated thumbnail image

    Raises:
        HTTPException: 404 if listing or image not found
        HTTPException: 403 if user is not the seller
        HTTPException: 400 if image doesn't belong to the listing
    """
    try:
        listing_uuid = uuid.UUID(listing_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid listing ID format"
        ) from exc

    updated_image = ListingImageService.set_thumbnail(
        db, listing_uuid, request.image_id, current_user
    )
    return ImagePublic.model_validate(updated_image)
