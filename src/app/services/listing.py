"""
Listing service.

This module contains business logic for listing operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.security import ensure_listing_owner_or_admin
from app.repository.listing import ListingRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.core.enums import UserRole
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
        user_role: UserRole,
        listing: ListingUpdate,
    ) -> Listing:
        """
        Update listing fields with validation and authorization check.

        Admins can update any listing, users can only update their own listings.

        Args:
            db: Database session
            listing_id: Listing ID to update
            user_id: User ID attempting the update
            user_role: Role of the user (USER or ADMIN)
            listing: Listing update data (only provided fields will be updated)

        Returns:
            Listing: Updated listing

        Raises:
            HTTPException: If listing not found or user is not authorized
        """
        db_listing = ListingRepository.get_by_id(db, listing_id)
        if not db_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing with ID {listing_id} not found",
            )
        ensure_listing_owner_or_admin(db_listing, user_id, user_role)
        return ListingRepository.update(db, db_listing, listing)

    def delete(
        self, db: Session, listing_id: uuid.UUID, user_id: uuid.UUID, user_role: UserRole
    ) -> None:
        """
        Permanently delete a listing with validation and authorization check.

        Admins can delete any listing, users can only delete their own listings.

        Args:
            db: Database session
            listing_id: Listing ID (UUID) to delete
            user_id: User ID attempting the delete
            user_role: Role of the user (USER or ADMIN)

        Raises:
            HTTPException: If listing not found or user is not authorized
        """
        db_listing = ListingRepository.get_by_id(db, listing_id)
        if not db_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing with ID {listing_id} not found",
            )
        ensure_listing_owner_or_admin(db_listing, user_id, user_role)
        ListingRepository.delete(db, db_listing)


# Create a singleton instance
listing_service = ListingService()
