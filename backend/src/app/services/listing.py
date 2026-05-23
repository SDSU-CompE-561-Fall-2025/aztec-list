"""
Listing service.

This module contains business logic for listing operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.llm import expand_query
from app.core.logging_safe import sanitize_log
from app.core.security import ensure_resource_owner
from app.core.settings import settings
from app.core.storage import delete_listing_images
from app.repository.listing import ListingRepository
from app.services.vector_store import ListingFilter, vector_store

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

logger = logging.getLogger(__name__)

# Max semantic candidates pulled from the vector store before in-app pagination.
SEMANTIC_CANDIDATE_LIMIT = 50


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
    ) -> tuple[list[Listing], int]:
        """
        Get all listings by seller ID with pagination and sorting.

        Args:
            db: Database session
            seller_id: User ID of the seller
            params: Pagination and filtering parameters

        Returns:
            tuple[list[Listing], int]: Filtered listings and total count
        """
        listings = ListingRepository.get_by_seller(db, seller_id, params)
        count = ListingRepository.count_by_seller(db, seller_id, params)
        return listings, count

    def get_filtered(self, db: Session, params: ListingSearchParams) -> tuple[list[Listing], int]:
        """
        Get listings with filters, pagination, and sorting.

        Uses AI semantic search when requested (and enabled); otherwise falls back to
        the keyword (ILIKE) search in the repository.

        Args:
            db: Database session
            params: Search parameters (filters, pagination, sorting)

        Returns:
            tuple[list[Listing], int]: Matching listings and total count
        """
        if self._use_semantic_search(params):
            return self._semantic_search(db, params)

        listings = ListingRepository.get_filtered(db, params)
        count = ListingRepository.count_filtered(db, params)
        return listings, count

    @staticmethod
    def _use_semantic_search(params: ListingSearchParams) -> bool:
        """Semantic search runs only when enabled, requested, and given query text."""
        return bool(settings.ai.enabled and params.semantic and params.search_text)

    def _semantic_search(
        self, db: Session, params: ListingSearchParams
    ) -> tuple[list[Listing], int]:
        """Rank listings by embedding similarity, degrading to keyword search on failure."""
        listing_filter = ListingFilter(
            category=params.category,
            condition=params.condition,
            min_price=params.min_price,
            max_price=params.max_price,
            seller_id=params.seller_id,
        )
        try:
            hits = vector_store.search(
                expand_query(params.search_text or ""),
                limit=SEMANTIC_CANDIDATE_LIMIT,
                score_threshold=settings.vector.score_floor,
                listing_filter=listing_filter,
            )
        except Exception:  # degrade gracefully to keyword search
            logger.exception("Semantic search failed; falling back to keyword search")
            listings = ListingRepository.get_filtered(db, params)
            return listings, ListingRepository.count_filtered(db, params)

        # Resolve to real, active listings first - this drops stale/orphan vectors (deleted or
        # deactivated listings still in the index) so they cannot skew the cutoff or the count.
        scores = dict(hits)
        matches = ListingRepository.get_by_ids(db, list(scores))
        # Relative cutoff against the best REAL hit: keep listings within `relative_margin` of it.
        if matches:
            cutoff = scores[matches[0].id] - settings.vector.relative_margin
            matches = [m for m in matches if scores[m.id] >= cutoff]
        total = len(matches)
        page = matches[params.offset : params.offset + params.limit]
        for listing in page:
            # Transient attribute surfaced by ListingSummary.relevance_score (from_attributes).
            listing.relevance_score = scores.get(listing.id)
        return page, total

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
        db_listing = ListingRepository.create(db, seller_id, listing)
        self._index_listing(db_listing)
        return db_listing

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
        ensure_resource_owner(db_listing.seller_id, user_id, "listing")
        updated = ListingRepository.update(db, db_listing, listing)
        self._index_listing(updated)
        return updated

    def delete(self, db: Session, listing_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Permanently delete a listing (owner only).

        Only the listing owner can delete their own listing.
        Admins must use the admin endpoints to remove listings.
        Also deletes all associated images from the filesystem.

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
        ensure_resource_owner(db_listing.seller_id, user_id, "listing")

        # Delete from database first (images table CASCADE will handle DB cleanup)
        ListingRepository.delete(db, db_listing)

        # Then delete physical files from filesystem
        delete_listing_images(listing_id)

        # Finally remove the vector from the search index
        self._deindex_listing(listing_id)

    @staticmethod
    def _index_listing(listing: Listing) -> None:
        """Upsert a listing's embedding. Indexing failures must not break listing writes."""
        if not settings.ai.enabled:
            return
        try:
            vector_store.upsert_listing(listing)
        except Exception:  # eventual consistency; repair via reindex script
            logger.exception("Failed to index listing %s in vector store", sanitize_log(listing.id))

    @staticmethod
    def _deindex_listing(listing_id: uuid.UUID) -> None:
        """Remove a listing's embedding. Failures must not break deletion."""
        if not settings.ai.enabled:
            return
        try:
            vector_store.delete_listing(listing_id)
        except Exception:  # eventual consistency; repair via reindex script
            logger.exception(
                "Failed to remove listing %s from vector store", sanitize_log(listing_id)
            )


# Create a singleton instance
listing_service = ListingService()
