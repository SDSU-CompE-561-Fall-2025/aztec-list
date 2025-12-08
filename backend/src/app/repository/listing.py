"""
Listing repository.

This module provides data access layer for listing operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.enums import ListingSortOrder
from app.models.listing import Listing

if TYPE_CHECKING:
    import uuid

    from sqlalchemy import Select
    from sqlalchemy.orm import Session

    from app.schemas.listing import (
        ListingCreate,
        ListingSearchParams,
        ListingUpdate,
        UserListingsParams,
    )


class ListingRepository:
    """Repository for listing data access."""

    @staticmethod
    def _apply_seller_filters(
        seller_id: uuid.UUID, params: UserListingsParams
    ) -> Select[tuple[Listing]]:
        query = select(Listing).where(Listing.seller_id == seller_id)

        if not params.include_inactive:
            query = query.where(Listing.is_active)

        if params.sort == ListingSortOrder.PRICE_ASC:
            query = query.order_by(Listing.price.asc(), Listing.created_at.desc())
        elif params.sort == ListingSortOrder.PRICE_DESC:
            query = query.order_by(Listing.price.desc(), Listing.created_at.desc())
        else:  # ListingSortOrder.RECENT (default)
            query = query.order_by(Listing.created_at.desc())

        return query

    @staticmethod
    def _apply_search_filters(params: ListingSearchParams) -> Select[tuple[Listing]]:
        query = select(Listing).where(Listing.is_active)

        if params.search_text:
            # Full-text search over title and description
            # Escape SQL wildcards (%, _) to prevent wildcard injection
            escaped_query = (
                params.search_text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            search_filter = or_(
                Listing.title.ilike(f"%{escaped_query}%", escape="\\"),
                Listing.description.ilike(f"%{escaped_query}%", escape="\\"),
            )
            query = query.where(search_filter)

        if params.category:
            query = query.where(Listing.category == params.category)

        if params.min_price is not None:
            query = query.where(Listing.price >= params.min_price)

        if params.max_price is not None:
            query = query.where(Listing.price <= params.max_price)

        if params.condition:
            query = query.where(Listing.condition == params.condition)

        if params.seller_id:
            query = query.where(Listing.seller_id == params.seller_id)

        if params.sort == ListingSortOrder.PRICE_ASC:
            query = query.order_by(Listing.price.asc(), Listing.created_at.desc())
        elif params.sort == ListingSortOrder.PRICE_DESC:
            query = query.order_by(Listing.price.desc(), Listing.created_at.desc())
        else:  # ListingSortOrder.RECENT (default)
            query = query.order_by(Listing.created_at.desc())

        return query

    @staticmethod
    def get_by_id(db: Session, listing_id: uuid.UUID) -> Listing | None:
        """
        Get listing by ID with images eagerly loaded.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            Listing | None: Listing if found, None otherwise
        """
        return db.scalar(
            select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.images))
        )

    @staticmethod
    def get_by_seller(
        db: Session, seller_id: uuid.UUID, params: UserListingsParams
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
        query = ListingRepository._apply_seller_filters(seller_id, params)

        # Apply offset-based pagination
        # TODO: Implement cursor-based pagination in the future for better performance at scale
        query = query.offset(params.offset).limit(params.limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_by_seller(db: Session, seller_id: uuid.UUID, params: UserListingsParams) -> int:
        """
        Get all listings by seller ID with pagination and sorting.

        Args:
            db: Database session
            seller_id: User ID of the seller
            params: Pagination and filtering parameters

        Returns:
            list[Listing]: List of listings (empty if none found)
        """
        query = ListingRepository._apply_seller_filters(seller_id, params)
        return db.scalar(select(func.count()).select_from(query.subquery())) or 0

    @staticmethod
    def get_filtered(db: Session, params: ListingSearchParams) -> list[Listing]:
        """
        Get listings with filters, pagination, and sorting.

        Args:
            db: Database session
            params: Search parameters including filters, pagination, and sort options

        Returns:
            list[Listing]: List of matching listings (empty if none found)
        """
        query = ListingRepository._apply_search_filters(params)

        # Apply offset-based pagination
        # TODO: Implement cursor-based pagination in the future for better performance at scale
        query = query.offset(params.offset).limit(params.limit)

        return list(db.scalars(query).all())

    @staticmethod
    def count_filtered(db: Session, params: ListingSearchParams) -> int:
        """
        Get listings with filters, pagination, and sorting.

        Args:
            db: Database session
            params: Search parameters including filters, pagination, and sort options

        Returns:
            list[Listing]: List of matching listings (empty if none found)
        """
        query = ListingRepository._apply_search_filters(params)
        return db.scalar(select(func.count()).select_from(query.subquery())) or 0

    @staticmethod
    def create(db: Session, seller_id: uuid.UUID, listing: ListingCreate) -> Listing:
        """
        Create a new listing.

        Args:
            db: Database session
            seller_id: User ID of the seller
            listing: Listing creation data

        Returns:
            Listing: Created listing
        """
        db_listing = Listing(
            seller_id=seller_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            category=listing.category,
            condition=listing.condition,
        )
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)
        return db_listing

    @staticmethod
    def update(db: Session, db_listing: Listing, listing: ListingUpdate) -> Listing:
        """
        Update listing fields.

        Args:
            db: Database session
            db_listing: Listing instance to update
            listing: Listing update data (only provided fields will be updated)

        Returns:
            Listing: Updated listing
        """
        # Convert ListingUpdate model fields into dictionary
        update_data = listing.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_listing, field, value)

        db.commit()
        db.refresh(db_listing)
        return db_listing

    @staticmethod
    def delete(db: Session, db_listing: Listing) -> None:
        """
        Permanently delete listing from database and commit immediately.

        Args:
            db: Database session
            db_listing: Listing instance to delete
        """
        db.delete(db_listing)
        db.commit()

    @staticmethod
    def delete_no_commit(db: Session, db_listing: Listing) -> None:
        """
        Permanently delete listing without committing (for transactional operations).

        Args:
            db: Database session
            db_listing: Listing instance to delete
        """
        db.delete(db_listing)
        db.flush()
