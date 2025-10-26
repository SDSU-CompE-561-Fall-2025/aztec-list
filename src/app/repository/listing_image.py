"""
Listing image repository.

Provides data access functions for images associated with listings.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.listing import Listing
from app.models.listing_image import Image
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
        Get all images for a given listing.

        Args:
                db: Database session
                listing_id: Listing ID (UUID)

        Returns:
                list[Image]: List of images (empty if none found)
        """
        query = select(Image).where(Image.listing_id == listing_id).order_by(Image.created_at.asc())
        return list(db.scalars(query).all())

    @staticmethod
    def create(db: Session, image: ImageCreate) -> Image:
        """
        Create a new image for a listing.

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

        # If this image is marked as thumbnail, update the listing thumbnail_url
        if db_image.is_thumbnail:
            db_listing = db.get(Listing, db_image.listing_id)
            if db_listing:
                db_listing.thumbnail_url = db_image.url
                db.commit()
                db.refresh(db_listing)

        return db_image

    @staticmethod
    def update(db: Session, db_image: Image, image_update: ImageUpdate) -> Image:
        """
        Update image fields.

        Args:
                db: Database session
                db_image: Image instance to update
                image_update: Image update data (only provided fields will be updated)

        Returns:
                Image: Updated image
        """
        update_data = image_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_image, field, value)

        db.commit()
        db.refresh(db_image)

        # Ensure listing.thumbnail_url matches if thumbnail flag updated
        if "is_thumbnail" in update_data:
            db_listing = db.get(Listing, db_image.listing_id)
            if db_listing:
                if db_image.is_thumbnail:
                    db_listing.thumbnail_url = db_image.url
                elif db_listing.thumbnail_url == db_image.url:
                    db_listing.thumbnail_url = None
                db.commit()
                db.refresh(db_listing)

        return db_image

    @staticmethod
    def delete(db: Session, db_image: Image) -> None:
        """
        Delete image.

        Args:
                db: Database session
                db_image: Image instance to delete
        """
        # If deleting the thumbnail, clear listing thumbnail_url
        if db_image.is_thumbnail:
            db_listing = db.get(Listing, db_image.listing_id)
            if db_listing and db_listing.thumbnail_url == db_image.url:
                db_listing.thumbnail_url = None
                db.commit()

        db.delete(db_image)
        db.commit()

    @staticmethod
    def set_thumbnail(db: Session, db_image: Image) -> Image:
        """
        Mark an image as the listing thumbnail and update the listing record.

        This will unset the previous thumbnail if present.
        """
        # Unset existing thumbnails for the listing
        images = ListingImageRepository.get_by_listing(db, db_image.listing_id)
        for img in images:
            if img.is_thumbnail and img.id != db_image.id:
                img.is_thumbnail = False
        db.commit()

        # Set this image as thumbnail
        db_image.is_thumbnail = True
        db.commit()
        db.refresh(db_image)

        db_listing = db.get(Listing, db_image.listing_id)
        if db_listing:
            db_listing.thumbnail_url = db_image.url
            db.commit()
            db.refresh(db_listing)

        return db_image
