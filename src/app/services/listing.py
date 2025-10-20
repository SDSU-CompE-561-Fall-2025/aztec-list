"""
User service.

This module contains business logic for user operations.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.listing import Listing
from app.repository.listing import ListingRepository
from app.schemas.listing import ListingCreate


class ListingService:
    def get_listing_by_id(self, db: Session, listing_id: uuid.UUID) -> Listing:
        listing = ListingRepository.get_listing_by_id(db, listing_id)
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing with id '{listing_id}' not found",
            )
        return listing

    def get_user_listings(self, db: Session, user_id: uuid.UUID) -> list[Listing]:
        listings = ListingRepository.get_user_listings(db, user_id)
        if not listings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing from this user not found",  # noqa: F541
            )
        return listings

    def create(self, db: Session, listing: ListingCreate) -> Listing:
        existing_listing = ListingRepository.get_listing_by_id(db, listing.id)
        if existing_listing:
            pass
