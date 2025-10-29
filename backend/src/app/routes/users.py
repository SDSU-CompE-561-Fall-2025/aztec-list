import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.listing import ListingSearchResponse, ListingSummary, UserListingsParams
from app.schemas.user import UserPublic
from app.services.listing import listing_service
from app.services.user import user_service

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@user_router.get("/{user_id}", summary="Get a user's public profile", response_model=UserPublic)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get public user profile by ID.

    Args:
        user_id: The user's unique identifier (UUID)
        db: Database session

    Returns:
        UserPublic: Public user information

    Raises:
        HTTPException: 404 if user not found, 500 on database error
    """
    return user_service.get_by_id(db, user_id)


@user_router.get("/{user_id}/listings", summary="Get user's listings")
async def get_user_listings(
    user_id: uuid.UUID,
    params: Annotated[UserListingsParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> ListingSearchResponse:
    """
    Get paginated listings for a specific user.

    Args:
        user_id: The user's unique identifier (UUID)
        params: Query parameters including pagination (limit, offset),
                sorting (sort), and filters (include_inactive)
        db: Database session

    Returns:
        ListingSearchResponse: Paginated list of user's listings with total count

    Raises:
        HTTPException: 404 if user not found, 500 on database error
    """
    listings, count = listing_service.get_by_seller(db, user_id, params)

    return ListingSearchResponse(
        items=[ListingSummary.model_validate(listing) for listing in listings],
        next_cursor=None,
        count=count,
    )
