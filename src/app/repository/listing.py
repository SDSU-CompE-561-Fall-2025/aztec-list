"""
Listing Repository.

This module provides the data access layer for listing operations.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingUpdate


class ListingRepository:
    """Repository for listing data access."""

    @staticmethod
    def get_listings(db: Session) -> list[Listing]:
        pass

    @staticmethod
    def get_listing_by_id(db: Session, listing_id: uuid.UUID) -> Listing:
        pass

    @staticmethod
    def get_user_listings(db: Session, user_id: uuid.UUID) -> list[Listing]:
        pass

    @staticmethod
    def create(db: Session, listing: ListingCreate) -> Listing:
        pass

    @staticmethod
    def update(
        db: Session, listing_id: uuid.UUID, user_id: uuid.UUID, listing: ListingUpdate
    ) -> Listing:
        pass

    @staticmethod
    def delete(db: Session, user_id: uuid.UUID, listing: Listing) -> None:
        pass
