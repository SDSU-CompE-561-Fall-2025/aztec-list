import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.listing_image import Image
from app.models.user import User
from app.schemas.listing_image import ImageCreate, ImagePublic, ImageUpdate
from app.services.listing_images import listing_image_service

listing_images_router = APIRouter(
    prefix="/listings",
    tags=["Listing Images"],
)


@listing_images_router.get(
    "/{listing_id}/images",
    summary="List all images for a listing",
    response_model=list[ImagePublic],
)
async def list_images(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[Image]:
    """
    List all images for a listing.

    Images are returned in display order.

    Args:
        listing_id: Listing UUID
        db: Database session

    Returns:
        list[Image]: List of images for the listing

    Raises:
        HTTPException: 404 if listing not found
    """
    return listing_image_service.get_by_listing(db, listing_id)


@listing_images_router.post(
    "/{listing_id}/images",
    summary="Add an image to a listing",
    status_code=status.HTTP_201_CREATED,
    response_model=ImagePublic,
)
async def create_image(
    listing_id: uuid.UUID,
    image: ImageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Image:
    """
    Create a new image for a listing.

    Only the listing seller may add images.

    Args:
        listing_id: Listing UUID from path
        image: Image data to create
        current_user: Authenticated user
        db: Database session

    Returns:
        Image: The created image

    Raises:
        HTTPException: 400 if listing_id mismatch, 403 if not seller, 404 if listing not found
    """
    return listing_image_service.create(db, listing_id, current_user.id, image)


@listing_images_router.get(
    "/{listing_id}/images/{image_id}",
    summary="Get a single image",
    response_model=ImagePublic,
)
async def get_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Image:
    """
    Get a single image by ID.

    Args:
        listing_id: Listing UUID
        image_id: Image UUID
        db: Database session

    Returns:
        Image: The requested image

    Raises:
        HTTPException: 404 if image not found or doesn't belong to listing
    """
    return listing_image_service.get_by_id(db, listing_id, image_id)


@listing_images_router.patch(
    "/{listing_id}/images/{image_id}",
    summary="Update an image",
    response_model=ImagePublic,
)
async def update_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    image_update: ImageUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Image:
    """
    Update an image.

    Only the listing owner may update images.

    Args:
        listing_id: Listing UUID
        image_id: Image UUID
        image_update: Fields to update
        current_user: Authenticated user
        db: Database session

    Returns:
        Image: The updated image

    Raises:
        HTTPException: 403 if not seller, 404 if image/listing not found
    """
    return listing_image_service.update(db, listing_id, image_id, current_user.id, image_update)


@listing_images_router.delete(
    "/{listing_id}/images/{image_id}",
    summary="Delete an image",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Delete an image.

    Only the listing owner may delete images.

    Args:
        listing_id: Listing UUID
        image_id: Image UUID
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: 403 if not seller, 404 if image/listing not found
    """
    listing_image_service.delete(db, listing_id, image_id, current_user.id)


@listing_images_router.post(
    "/{listing_id}/images/{image_id}/thumbnail",
    summary="Set image as listing thumbnail",
    response_model=ImagePublic,
)
async def set_thumbnail(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Image:
    """
    Set an image as the listing thumbnail.

    Only the listing owner may do this. Only one image can be the thumbnail at a time.

    Args:
        listing_id: Listing UUID
        image_id: Image UUID to set as thumbnail
        current_user: Authenticated user
        db: Database session

    Returns:
        Image: The updated image with is_thumbnail=True

    Raises:
        HTTPException: 403 if not seller, 404 if image/listing not found
    """
    return listing_image_service.set_thumbnail(db, listing_id, image_id, current_user.id)
