"""
Listing image service.

This module provides business logic for listing image operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.security import ensure_resource_owner
from app.core.settings import settings
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

        listing = ListingRepository.get_by_id(db, image.listing_id)
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found for this image",
            )
        ensure_resource_owner(listing.seller_id, current_user.id, "image")

        return image

    @staticmethod
    def create(db: Session, listing_id: uuid.UUID, image: ImageCreate, current_user: User) -> Image:
        """
        Create a new image for a listing.

        Args:
            db: Database session
            listing_id: Listing ID from the URL path
            image: Image creation data (url, is_thumbnail, alt_text)
            current_user: Current authenticated user

        Returns:
            Image: Created image

        Raises:
            HTTPException: 404 if listing not found
            HTTPException: 403 if user is not the seller
            HTTPException: 400 if max images exceeded
        """
        listing = ListingRepository.get_by_id(db, listing_id)
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
        ensure_resource_owner(listing.seller_id, current_user.id, "listing")

        current_count = ListingImageRepository.count_by_listing(db, listing_id)
        if current_count >= settings.listing.max_images_per_listing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {settings.listing.max_images_per_listing} images per listing",
            )

        should_be_thumbnail = current_count == 0 or image.is_thumbnail

        if should_be_thumbnail and current_count > 0:
            ListingImageRepository.clear_thumbnail_for_listing(db, listing_id)

        db_image = ListingImageRepository.create(
            db, listing_id, str(image.url), should_be_thumbnail, image.alt_text
        )

        if should_be_thumbnail:
            ListingImageRepository.update_listing_thumbnail_url(db, listing_id, str(db_image.url))

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

        was_thumbnail = db_image.is_thumbnail

        if image_update.is_thumbnail is True:
            ListingImageRepository.clear_thumbnail_for_listing(db, db_image.listing_id)

        if image_update.is_thumbnail is False and was_thumbnail:
            ListingImageRepository.update_listing_thumbnail_url(db, db_image.listing_id, None)

        updated_image = ListingImageRepository.update(
            db,
            db_image,
            str(image_update.url) if image_update.url is not None else None,
            image_update.is_thumbnail,
            image_update.alt_text,
        )

        is_now_thumbnail = updated_image.is_thumbnail
        url_changed = image_update.url is not None

        if is_now_thumbnail and (
            image_update.is_thumbnail is True or (was_thumbnail and url_changed)
        ):
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

        ListingImageRepository.delete(db, db_image)

        if was_thumbnail:
            remaining_images = ListingImageRepository.get_by_listing(db, listing_id)

            if remaining_images:
                new_thumbnail = remaining_images[0]
                ListingImageRepository.set_as_thumbnail_only(db, new_thumbnail)
                ListingImageRepository.update_listing_thumbnail_url(
                    db, listing_id, str(new_thumbnail.url)
                )
            else:
                ListingImageRepository.update_listing_thumbnail_url(db, listing_id, None)
