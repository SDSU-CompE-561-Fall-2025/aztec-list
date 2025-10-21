"""
Listing repository.

This module provides data access layer for listing operations.
"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.enums import ListingSortOrder
from app.models.listing import Listing
from app.schemas.listing import (
    ListingCreate,
    ListingSearchParams,
    ListingUpdate,
    UserListingsParams,
)


class ListingRepository:
    """Repository for listing data access."""

    @staticmethod
    def get_by_id(db: Session, listing_id: uuid.UUID) -> Listing | None:
        """
        Get listing by ID.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            Listing | None: Listing if found, None otherwise
        """
        return db.get(Listing, listing_id)

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
        query = select(Listing).where(Listing.seller_id == seller_id)

        # Filter by active status unless include_inactive is True
        if not params.include_inactive:
            query = query.where(Listing.is_active)

        # Apply sorting
        if params.sort == ListingSortOrder.PRICE_ASC:
            query = query.order_by(Listing.price.asc(), Listing.created_at.desc())
        elif params.sort == ListingSortOrder.PRICE_DESC:
            query = query.order_by(Listing.price.desc(), Listing.created_at.desc())
        else:  # default to RECENT
            query = query.order_by(Listing.created_at.desc())

        # Apply offset-based pagination
        # Implement cursor-based pagination in the future for better performance at scale
        query = query.offset(params.offset).limit(params.limit)
        return list(db.scalars(query).all())

    @staticmethod
    def search(db: Session, params: ListingSearchParams) -> list[Listing]:
        """
        Search listings with filters, pagination, and sorting.

        Args:
            db: Database session
            params: Search parameters including filters, pagination, and sort options

        Returns:
            list[Listing]: List of matching listings (empty if none found)
        """
        query = select(Listing).where(Listing.is_active)

        # Apply filters
        if params.q:
            # Full-text search over title and description
            search_filter = or_(
                Listing.title.ilike(f"%{params.q}%"),
                Listing.description.ilike(f"%{params.q}%"),
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

        # Apply sorting
        if params.sort == ListingSortOrder.PRICE_ASC:
            query = query.order_by(Listing.price.asc(), Listing.created_at.desc())
        elif params.sort == ListingSortOrder.PRICE_DESC:
            query = query.order_by(Listing.price.desc(), Listing.created_at.desc())
        else:  # default to RECENT
            query = query.order_by(Listing.created_at.desc())

        # Apply offset-based pagination
        # Implement cursor-based pagination in the future for better performance at scale
        query = query.offset(params.offset).limit(params.limit)

        return list(db.scalars(query).all())

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

        # Update db with direct assignment
        if "title" in update_data:
            db_listing.title = update_data["title"]
        if "description" in update_data:
            db_listing.description = update_data["description"]
        if "price" in update_data:
            db_listing.price = update_data["price"]
        if "category" in update_data:
            db_listing.category = update_data["category"]
        if "condition" in update_data:
            db_listing.condition = update_data["condition"]
        if "thumbnail_url" in update_data:
            db_listing.thumbnail_url = update_data["thumbnail_url"]
        if "is_active" in update_data:
            db_listing.is_active = update_data["is_active"]

        db.commit()
        db.refresh(db_listing)
        return db_listing

    @staticmethod
    def delete(db: Session, db_listing: Listing) -> None:
        """
        Delete listing.

        Args:
            db: Database session
            db_listing: Listing instance to delete
        """
        db.delete(db_listing)
        db.commit()
