import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models import Listing
from app.schemas.listing import (
    ListingCreate,
    ListingPublic,
    ListingSearchParams,
    ListingUpdate,
)
from app.services.listing import listing_service

listing_router = APIRouter(
    prefix="/listings",
    tags=["Listing"],
)


@listing_router.post(
    "/",
    summary="Create a new listing",
    response_model=ListingPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_listing(
    listing: ListingCreate,
    seller_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> Listing:
    """
    Create a new item listing for sale.

    Args:
        listing: Listing creation data (title, description, price, category, condition)
        seller_id: Authenticated user's ID from the JWT token (automatically set as seller)
        db: Database session

    Returns:
        ListingPublic: Created listing information

    Raises:
        HTTPException: 401 if not authenticated, 400 if validation fails
    """
    return listing_service.create(db, seller_id, listing)


@listing_router.get(
    "/{listing_id}",
    summary="Get a listing by ID",
    response_model=ListingPublic,
    status_code=status.HTTP_200_OK,
)
async def get_listing_by_id(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Listing:
    """
    Retrieve details of a single listing by its unique ID.

    Args:
        listing_id: Unique identifier of the listing to fetch
        db: Database session

    Returns:
        ListingPublic: Listing details including title, price, description, seller info

    Raises:
        HTTPException: 404 if listing not found
    """
    return listing_service.get_by_id(db, listing_id)


@listing_router.patch(
    "/{listing_id}",
    summary="Update a listing (owner only)",
    response_model=ListingPublic,
    status_code=status.HTTP_200_OK,
)
async def update_listing(
    listing_id: uuid.UUID,
    listing: ListingUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Listing:
    """
    Update an existing listing's details.

    All fields are optional; only provided fields will be updated.
    The is_active field can be toggled to temporarily hide the listing.

    Args:
        listing_id: ID of the listing to update
        listing: Listing update data (any combination of title, description, price, etc.)
        db: Database session

    Returns:
        ListingPublic: Updated listing information

    Raises:
        HTTPException: 404 if listing not found, 400 if validation fails
    """
    return listing_service.update(db, listing_id, listing)


@listing_router.delete(
    "/{listing_id}",
    summary="Delete a listing (owner or admin)",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_listing_by_id(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Permanently delete a listing.

    This is a hard delete that removes the listing from the database.
    For temporary hiding, use PATCH to set is_active to false instead.

    Args:
        listing_id: ID of the listing to delete
        db: Database session

    Returns:
        None: Returns 204 No Content on success

    Raises:
        HTTPException: 404 if listing not found, 401 if not authenticated
    """
    listing_service.delete(db, listing_id)


@listing_router.get(
    "/",
    summary="Search and filter listings",
    response_model=list[ListingPublic],
    status_code=status.HTTP_200_OK,
)
async def get_listings(
    params: Annotated[ListingSearchParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> list[Listing]:
    """
    Retrieve a paginated list of active listings with optional filters.

    Supports full-text search, category filtering, price range filtering,
    condition filtering, seller filtering, sorting, and pagination.

    Args:
        params: Search and filter parameters (q, category, price range, condition, seller_id, etc.)
        db: Database session

    Returns:
        list[ListingPublic]: List of matching listings (empty list if none found)

    Raises:
        HTTPException: 400 if invalid parameters
    """
    return listing_service.search(db, params)
