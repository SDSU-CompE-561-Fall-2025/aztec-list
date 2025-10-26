"""
Listing images service.

Business logic for listing image operations. This wraps repository calls and
performs validation (existence, ownership) using the listing service.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.listing_image import Image
from app.repository.listing_image import ListingImageRepository
from app.schemas.listing_image import ImageCreate, ImageUpdate
from app.services.listing import listing_service


class ListingImageService:
    """Service for listing image business logic."""

    def get_by_id(self, db: Session, image_id: uuid.UUID) -> Image:
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )
        return db_image

    def get_by_listing(self, db: Session, listing_id: uuid.UUID) -> list[Image]:
        # ensure listing exists (will raise 404 via listing_service)
        listing_service.get_by_id(db, listing_id)
        return ListingImageRepository.get_by_listing(db, listing_id)

    def create(self, db: Session, seller_id: uuid.UUID, image: ImageCreate) -> Image:
        # Ensure listing exists and seller owns it
        listing = listing_service.get_by_id(db, image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not listing owner",
            )

        return ListingImageRepository.create(db, image)

    def update(
        self, db: Session, image_id: uuid.UUID, seller_id: uuid.UUID, image_update: ImageUpdate
    ) -> Image:
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        listing = listing_service.get_by_id(db, db_image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not listing owner")

        return ListingImageRepository.update(db, db_image, image_update)

    def delete(self, db: Session, image_id: uuid.UUID, seller_id: uuid.UUID) -> None:
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        listing = listing_service.get_by_id(db, db_image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not listing owner")

        ListingImageRepository.delete(db, db_image)

    def set_thumbnail(self, db: Session, image_id: uuid.UUID, seller_id: uuid.UUID) -> Image:
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        listing = listing_service.get_by_id(db, db_image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not listing owner")

        return ListingImageRepository.set_thumbnail(db, db_image)


# Singleton instance
listing_image_service = ListingImageService()
