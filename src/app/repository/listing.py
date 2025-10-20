"""
Listing Repository.

This module provides the data access layer for listing operations.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingUpdate


class ListingRepository:
    """Repository for listing data access."""

    # figure out how to implement this pagination based retrieval we need to do
    @staticmethod
    def get_listings(db: Session, number_of_listings_to_get: int) -> list[Listing] | None:
        pass

    @staticmethod
    def get_listing_by_id(db: Session, listing_id: uuid.UUID) -> Listing | None:
        query = select(Listing).where(Listing.id == listing_id)
        return db.scalars(query).first()

    # may have to add some limiter and again how many listings do we display per page
    # if the user has an insane amount of listings
    @staticmethod
    def get_user_listings(db: Session, user_id: uuid.UUID) -> list[Listing] | None:
        query = select(Listing).where(Listing.user_id == user_id)
        return db.scalars(query).all

    @staticmethod
    def create(db: Session, listing: ListingCreate) -> Listing:
        db_listing = Listing(
            title=listing.title,
            price=listing.price,
            category=listing.category,
            condition=listing.condition,
            is_active=listing.is_active,
            description=listing.description,
            thumbnail_url=listing.thumbnail_url,
        )
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)
        return db_listing

    @staticmethod
    def update(db: Session, db_listing: Listing, listing_update: ListingUpdate) -> Listing:
        update_data = listing_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_listing, field, value)
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)
        return db_listing

    @staticmethod
    def delete(db: Session, listing: Listing) -> None:
        db.delete(listing)
        db.commit()

    # first have to go back into user and add an is_admin field to then do this
    @staticmethod
    def admin_delete(
        db: Session, user_id: uuid.UUID, listing_id: uuid.UUID, listing: Listing
    ) -> None:
        pass
