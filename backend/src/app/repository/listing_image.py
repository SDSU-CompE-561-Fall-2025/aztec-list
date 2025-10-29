"""
Listing image repository.

This module provides data access layer for listing image operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from app.models.listing import Listing
from app.models.listing_image import Image

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.schemas.listing_image import ImageCreate, ImageUpdate


class ListingImageRepository:
    """Repository for listing image data access."""

    @staticmethod
    def get_by_id(db: Session, image_id: uuid.UUID) -> Image | None:
        """
        Get image by ID.

        Args:
            db: Database session
            image_id: Image ID (UUID)

        Returns:
            Image | None: Image if found, None otherwise
        """
        return db.get(Image, image_id)

    @staticmethod
    def get_by_listing(db: Session, listing_id: uuid.UUID) -> list[Image]:
        """
        Get all images for a listing, ordered by display order.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            list[Image]: List of images (empty if none found)
        """
        query = select(Image).where(Image.listing_id == listing_id).order_by(Image.created_at.asc())
        return list(db.scalars(query).all())

    @staticmethod
    def get_thumbnail(db: Session, listing_id: uuid.UUID) -> Image | None:
        """
        Get the thumbnail image for a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            Image | None: Thumbnail image if found, None otherwise
        """
        query = select(Image).where(Image.listing_id == listing_id, Image.is_thumbnail)
        return db.scalars(query).first()

    @staticmethod
    def create(db: Session, image: ImageCreate) -> Image:
        """
        Create a new image.

        Args:
            db: Database session
            image: Image creation data

        Returns:
            Image: Created image
        """
        db_image = Image(
            listing_id=image.listing_id,
            url=image.url,
            is_thumbnail=image.is_thumbnail,
            alt_text=image.alt_text,
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def update(db: Session, db_image: Image, image_update: ImageUpdate) -> Image:
        """
        Update an existing image.

        Args:
            db: Database session
            db_image: Existing image object
            image_update: Fields to update

        Returns:
            Image: Updated image
        """
        update_data = image_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_image, field, value)

        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def delete(db: Session, db_image: Image) -> None:
        """
        Delete an image.

        Args:
            db: Database session
            db_image: Image object to delete
        """
        db.delete(db_image)
        db.commit()

    @staticmethod
    def clear_thumbnail_for_listing(db: Session, listing_id: uuid.UUID) -> None:
        """
        Clear the thumbnail flag from all images in a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)
        """
        stmt = (
            update(Image)
            .where(Image.listing_id == listing_id, Image.is_thumbnail == True)  # noqa: E712
            .values(is_thumbnail=False)
        )
        db.execute(stmt)
        db.commit()

    @staticmethod
    def set_thumbnail(db: Session, db_image: Image) -> Image:
        """
        Set an image as the thumbnail for its listing.

        Clears thumbnail flag from other images in the same listing.

        Args:
            db: Database session
            db_image: Image to set as thumbnail

        Returns:
            Image: Updated image
        """
        # Clear existing thumbnail
        ListingImageRepository.clear_thumbnail_for_listing(db, db_image.listing_id)

        # Set new thumbnail
        db_image.is_thumbnail = True
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def count_by_listing(db: Session, listing_id: uuid.UUID) -> int:
        """
        Count images for a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            int: Number of images
        """
        query = select(func.count()).select_from(Image).where(Image.listing_id == listing_id)
        return db.scalar(query) or 0

    @staticmethod
    def delete_all_for_listing(db: Session, listing_id: uuid.UUID) -> None:
        """
        Delete all images for a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)
        """
        stmt = delete(Image).where(Image.listing_id == listing_id)
        db.execute(stmt)
        db.commit()

    @staticmethod
    def set_as_thumbnail_only(db: Session, db_image: Image) -> Image:
        """
        Set an image as thumbnail without clearing other thumbnails.

        Used when you know no other thumbnails exist (e.g., after deletion).

        Args:
            db: Database session
            db_image: Image to set as thumbnail

        Returns:
            Image: Updated image
        """
        db_image.is_thumbnail = True
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def update_listing_thumbnail_url(
        db: Session, listing_id: uuid.UUID, thumbnail_url: str | None
    ) -> None:
        """
        Update the thumbnail_url field of a listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)
            thumbnail_url: New thumbnail URL (or None to clear)

        Raises:
            ValueError: If listing with given ID does not exist
        """
        listing = db.get(Listing, listing_id)
        if not listing:
            msg = (
                f"Cannot update thumbnail_url: Listing with ID {listing_id} not found. "
                "This may indicate a data integrity issue."
            )
            raise ValueError(msg)
        listing.thumbnail_url = thumbnail_url
        db.commit()
