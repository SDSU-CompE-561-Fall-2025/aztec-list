import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.listing_image import Image as ImageSchema
from app.schemas.listing_image import ImageCreate, ImageUpdate
from app.services.listing_images import listing_image_service

listing_images_router = APIRouter(
    prefix="/listings",
    tags=["Listing Images"],
)


@listing_images_router.get("/{listing_id}/images")
async def list_images(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[ImageSchema]:
    """List all images for a listing."""
    return listing_image_service.get_by_listing(db, listing_id)


@listing_images_router.post(
    "/{listing_id}/images",
    status_code=status.HTTP_201_CREATED,
)
async def create_image(
    listing_id: uuid.UUID,
    image: ImageCreate,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ImageSchema:
    """Create a new image for a listing. Only the seller may add images."""
    if image.listing_id != listing_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing ID in URL must match listing_id in image data",
        )
    return listing_image_service.create(db, user_id, image)


@listing_images_router.get("/{listing_id}/images/{image_id}")
async def get_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ImageSchema:
    """Get a single image by ID."""
    image = listing_image_service.get_by_id(db, image_id)
    if image.listing_id != listing_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found in listing {listing_id}",
        )
    return image


@listing_images_router.patch("/{listing_id}/images/{image_id}")
async def update_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    image_update: ImageUpdate,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ImageSchema:
    """Update an image. Only the listing owner may update images."""
    # First verify image exists and belongs to this listing
    image = listing_image_service.get_by_id(db, image_id)
    if image.listing_id != listing_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found in listing {listing_id}",
        )
    return listing_image_service.update(db, image_id, user_id, image_update)


@listing_images_router.delete(
    "/{listing_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete an image. Only the listing owner may delete images."""
    # First verify image exists and belongs to this listing
    image = listing_image_service.get_by_id(db, image_id)
    if image.listing_id != listing_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found in listing {listing_id}",
        )
    return listing_image_service.delete(db, image_id, user_id)


@listing_images_router.post("/{listing_id}/images/{image_id}/thumbnail")
async def set_thumbnail(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ImageSchema:
    """Set an image as the listing thumbnail. Only the listing owner may do this."""
    # First verify image exists and belongs to this listing
    image = listing_image_service.get_by_id(db, image_id)
    if image.listing_id != listing_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found in listing {listing_id}",
        )
    return listing_image_service.set_thumbnail(db, image_id, user_id)
