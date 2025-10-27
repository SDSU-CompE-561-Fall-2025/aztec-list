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

    def get_by_id(self, db: Session, listing_id: uuid.UUID, image_id: uuid.UUID) -> Image:
        """
        Get an image by ID and verify it belongs to the listing.

        Args:
            db: Database session
            listing_id: Expected listing ID
            image_id: Image ID to fetch

        Returns:
            Image: The image if found and belongs to listing

        Raises:
            HTTPException: 404 if image not found or doesn't belong to listing
        """
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        if db_image.listing_id != listing_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {image_id} not found in listing {listing_id}",
            )

        return db_image

    def get_by_listing(self, db: Session, listing_id: uuid.UUID) -> list[Image]:
        """
        Get all images for a listing.

        Args:
            db: Database session
            listing_id: Listing ID to fetch images for

        Returns:
            list[Image]: List of images for the listing

        Raises:
            HTTPException: 404 if listing not found
        """
        # ensure listing exists (will raise 404 via listing_service)
        listing_service.get_by_id(db, listing_id)
        return ListingImageRepository.get_by_listing(db, listing_id)

    def create(
        self, db: Session, listing_id: uuid.UUID, seller_id: uuid.UUID, image: ImageCreate
    ) -> Image:
        """
        Create a new image for a listing.

        Args:
            db: Database session
            listing_id: Listing ID from URL path
            seller_id: User ID of the seller
            image: Image data to create

        Returns:
            Image: The created image

        Raises:
            HTTPException: 400 if listing_id mismatch, 403 if not seller, 404 if listing not found
        """
        # Validate listing_id in body matches URL
        if image.listing_id != listing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Listing ID in URL must match listing_id in image data",
            )

        # Ensure listing exists and seller owns it
        listing = listing_service.get_by_id(db, image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not listing owner",
            )

        return ListingImageRepository.create(db, image)

    def update(
        self,
        db: Session,
        listing_id: uuid.UUID,
        image_id: uuid.UUID,
        seller_id: uuid.UUID,
        image_update: ImageUpdate,
    ) -> Image:
        """
        Update an image.

        Args:
            db: Database session
            listing_id: Listing ID from URL path
            image_id: Image ID to update
            seller_id: User ID of the seller
            image_update: Fields to update

        Returns:
            Image: The updated image

        Raises:
            HTTPException: 403 if not seller, 404 if image/listing not found or mismatch
        """
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        # Verify image belongs to the listing
        if db_image.listing_id != listing_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {image_id} not found in listing {listing_id}",
            )

        listing = listing_service.get_by_id(db, db_image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not listing owner")

        return ListingImageRepository.update(db, db_image, image_update)

    def delete(
        self, db: Session, listing_id: uuid.UUID, image_id: uuid.UUID, seller_id: uuid.UUID
    ) -> None:
        """
        Delete an image.

        Args:
            db: Database session
            listing_id: Listing ID from URL path
            image_id: Image ID to delete
            seller_id: User ID of the seller

        Raises:
            HTTPException: 403 if not seller, 404 if image/listing not found or mismatch
        """
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        # Verify image belongs to the listing
        if db_image.listing_id != listing_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {image_id} not found in listing {listing_id}",
            )

        listing = listing_service.get_by_id(db, db_image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not listing owner")

        ListingImageRepository.delete(db, db_image)

    def set_thumbnail(
        self, db: Session, listing_id: uuid.UUID, image_id: uuid.UUID, seller_id: uuid.UUID
    ) -> Image:
        """
        Set an image as the listing thumbnail.

        Only one image can be the thumbnail at a time.

        Args:
            db: Database session
            listing_id: Listing ID from URL path
            image_id: Image ID to set as thumbnail
            seller_id: User ID of the seller

        Returns:
            Image: The updated image with is_thumbnail=True

        Raises:
            HTTPException: 403 if not seller, 404 if image/listing not found or mismatch
        """
        db_image = ListingImageRepository.get_by_id(db, image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        # Verify image belongs to the listing
        if db_image.listing_id != listing_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {image_id} not found in listing {listing_id}",
            )

        listing = listing_service.get_by_id(db, db_image.listing_id)
        if listing.seller_id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not listing owner")

        return ListingImageRepository.set_thumbnail(db, db_image)


# Singleton instance
listing_image_service = ListingImageService()
