"""
Listing service.

This module contains business logic for listing operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.repository.listing import ListingRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.listing import Listing
    from app.schemas.listing import (
        ListingCreate,
        ListingSearchParams,
        ListingUpdate,
        UserListingsParams,
    )


class ListingService:
    """Service for listing business logic."""

    def get_by_id(self, db: Session, listing_id: uuid.UUID) -> Listing:
        """
        Get listing by ID with validation.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            Listing: Listing object

        Raises:
            HTTPException: If listing not found
        """
        listing = ListingRepository.get_by_id(db, listing_id)
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing with ID {listing_id} not found",
            )
        return listing

    def get_by_seller(
        self, db: Session, seller_id: uuid.UUID, params: UserListingsParams
    ) -> list[Listing]:
        """
        Get all listings by seller ID with pagination and sorting.

        Args:
            db: Database session
            seller_id: User ID of the seller
            params: Pagination and filtering parameters

        Returns:
            list[Listing]: List of listings (empty if none found)
        """
        return ListingRepository.get_by_seller(db, seller_id, params)

    def search(self, db: Session, params: ListingSearchParams) -> list[Listing]:
        """
        Search listings with filters, pagination, and sorting.

        Args:
            db: Database session
            params: Search parameters (filters, pagination, sorting)

        Returns:
            list[Listing]: List of matching listings (empty if none found)
        """
        return ListingRepository.search(db, params)

    def create(self, db: Session, seller_id: uuid.UUID, listing: ListingCreate) -> Listing:
        """
        Create a new listing with validation.

        Args:
            db: Database session
            seller_id: User ID of the seller
            listing: Listing creation data

        Returns:
            Listing: Created listing
        """
        return ListingRepository.create(db, seller_id, listing)

    def update(
        self,
        db: Session,
        listing_id: uuid.UUID,
        user_id: uuid.UUID,
        listing: ListingUpdate,
    ) -> Listing:
        """
        Update listing fields with validation and authorization check (owner only).

        Only the listing owner can update their own listing.
        Admins should use admin endpoints for moderation actions.

        Args:
            db: Database session
            listing_id: Listing ID to update
            user_id: User ID attempting the update (must be owner)
            listing: Listing update data (only provided fields will be updated)

        Returns:
            Listing: Updated listing

        Raises:
            HTTPException: If listing not found or user is not the owner
        """
        db_listing = ListingRepository.get_by_id(db, listing_id)
        if not db_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing with ID {listing_id} not found",
            )

        # Check authorization: owner only (admins must use admin endpoints)
        if db_listing.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can update their listing",
            )

        return ListingRepository.update(db, db_listing, listing)

    def delete(self, db: Session, listing_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Permanently delete a listing (owner only).

        Only the listing owner can delete their own listing.
        Admins must use the admin endpoints to remove listings.

        Args:
            db: Database session
            listing_id: Listing ID (UUID) to delete
            user_id: User ID attempting the delete (must be owner)

        Raises:
            HTTPException: If listing not found or user is not the owner
        """
        db_listing = ListingRepository.get_by_id(db, listing_id)
        if not db_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing with ID {listing_id} not found",
            )

        # Check authorization: owner only (admins must use admin endpoints)
        if db_listing.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can delete their listing",
            )

        ListingRepository.delete(db, db_listing)


# Create a singleton instance
listing_service = ListingService()
