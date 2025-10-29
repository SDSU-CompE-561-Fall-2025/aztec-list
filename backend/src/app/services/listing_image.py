"""
Listing image service.

This module provides business logic for listing image operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.repository.listing import ListingRepository
from app.repository.listing_image import ListingImageRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.listing_image import Image
    from app.models.user import User
    from app.schemas.listing_image import ImageCreate, ImageUpdate


class ListingImageService:
    """Service for listing image business logic."""

    MAX_IMAGES_PER_LISTING = 10

    @staticmethod
    def get_by_id(db: Session, image_id: uuid.UUID, current_user: User) -> Image:
        """
        Get an image by ID.

        Args:
            db: Database session
            image_id: Image ID (UUID)
            current_user: Current authenticated user

        Returns:
            Image: The image

        Raises:
            HTTPException: 404 if image not found
            HTTPException: 403 if user is not the seller of the listing
        """
        image = ListingImageRepository.get_by_id(db, image_id)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

        # Verify the user is the seller of the listing
        listing = ListingRepository.get_by_id(db, image.listing_id)
        if not listing or listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this image",
            )

        return image

    @staticmethod
    def get_by_listing(
        db: Session, listing_id: uuid.UUID, current_user: User | None = None
    ) -> list[Image]:
        """
        Get all images for a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)
            current_user: Optional current authenticated user (for ownership check)

        Returns:
            list[Image]: List of images

        Raises:
            HTTPException: 404 if listing not found
            HTTPException: 403 if user is not authorized (for non-public listings)
        """
        listing = ListingRepository.get_by_id(db, listing_id)
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

        # Optional: Check if listing is active or user is seller
        if current_user and not listing.is_active and listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this listing's images",
            )

        return ListingImageRepository.get_by_listing(db, listing_id)

    @staticmethod
    def create(db: Session, image: ImageCreate, current_user: User) -> Image:
        """
        Create a new image for a listing.

        Args:
            db: Database session
            image: Image creation data
            current_user: Current authenticated user

        Returns:
            Image: Created image

        Raises:
            HTTPException: 404 if listing not found
            HTTPException: 403 if user is not the seller
            HTTPException: 400 if max images exceeded
        """
        # Verify listing exists and user is the seller
        listing = ListingRepository.get_by_id(db, image.listing_id)
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
        if listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can add images to this listing",
            )

        # Check image count limit
        current_count = ListingImageRepository.count_by_listing(db, image.listing_id)
        if current_count >= ListingImageService.MAX_IMAGES_PER_LISTING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {ListingImageService.MAX_IMAGES_PER_LISTING} images per listing",
            )

        # Create the image
        db_image = ListingImageRepository.create(db, image)

        # If this is the first image or is_thumbnail is True, set as thumbnail
        if current_count == 0 or image.is_thumbnail:
            ListingImageRepository.set_thumbnail(db, db_image)
            # Update listing thumbnail_url
            ListingImageRepository.update_listing_thumbnail_url(
                db, image.listing_id, str(db_image.url)
            )

        return db_image

    @staticmethod
    def update(
        db: Session, image_id: uuid.UUID, image_update: ImageUpdate, current_user: User
    ) -> Image:
        """
        Update an existing image.

        Args:
            db: Database session
            image_id: Image ID (UUID)
            image_update: Fields to update
            current_user: Current authenticated user

        Returns:
            Image: Updated image

        Raises:
            HTTPException: 404 if image not found
            HTTPException: 403 if user is not the seller
        """
        db_image = ListingImageService.get_by_id(db, image_id, current_user)

        # Update the image
        updated_image = ListingImageRepository.update(db, db_image, image_update)

        # If is_thumbnail changed to True, update thumbnail
        if image_update.is_thumbnail is True:
            ListingImageRepository.set_thumbnail(db, updated_image)
            # Update listing thumbnail_url
            ListingImageRepository.update_listing_thumbnail_url(
                db, updated_image.listing_id, str(updated_image.url)
            )

        return updated_image

    @staticmethod
    def delete(db: Session, image_id: uuid.UUID, current_user: User) -> None:
        """
        Delete an image.

        If the deleted image was the thumbnail, automatically set another image
        as the thumbnail (if any exist).

        Args:
            db: Database session
            image_id: Image ID (UUID)
            current_user: Current authenticated user

        Raises:
            HTTPException: 404 if image not found
            HTTPException: 403 if user is not the seller
        """
        db_image = ListingImageService.get_by_id(db, image_id, current_user)
        listing_id = db_image.listing_id
        was_thumbnail = db_image.is_thumbnail

        # Delete the image
        ListingImageRepository.delete(db, db_image)

        # If it was the thumbnail, set a new one
        if was_thumbnail:
            remaining_images = ListingImageRepository.get_by_listing(db, listing_id)

            if remaining_images:
                # Set the first remaining image as thumbnail
                new_thumbnail = remaining_images[0]
                ListingImageRepository.set_thumbnail(db, new_thumbnail)
                ListingImageRepository.update_listing_thumbnail_url(
                    db, listing_id, str(new_thumbnail.url)
                )
            else:
                # No images left, clear thumbnail
                ListingImageRepository.update_listing_thumbnail_url(db, listing_id, None)

    @staticmethod
    def set_thumbnail(
        db: Session, listing_id: uuid.UUID, image_id: uuid.UUID, current_user: User
    ) -> Image:
        """
        Set an image as the thumbnail for a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)
            image_id: Image ID (UUID) to set as thumbnail
            current_user: Current authenticated user

        Returns:
            Image: The new thumbnail image

        Raises:
            HTTPException: 404 if listing or image not found
            HTTPException: 403 if user is not the seller
            HTTPException: 400 if image doesn't belong to the listing
        """
        # Verify listing exists and user is the seller
        listing = ListingRepository.get_by_id(db, listing_id)
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
        if listing.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can set the thumbnail",
            )

        # Get the image
        image = ListingImageRepository.get_by_id(db, image_id)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

        # Verify image belongs to the listing
        if image.listing_id != listing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image does not belong to this listing",
            )

        # Set as thumbnail
        updated_image = ListingImageRepository.set_thumbnail(db, image)

        # Update listing thumbnail_url
        ListingImageRepository.update_listing_thumbnail_url(db, listing_id, str(updated_image.url))

        return updated_image
