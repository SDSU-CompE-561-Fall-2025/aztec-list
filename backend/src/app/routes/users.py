import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_not_banned
from app.models.listing import Listing
from app.models.user import User
from app.schemas.listing import ListingPublic, UserListingsParams
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


@user_router.get(
    "/{user_id}/listings", summary="Get user's listings", response_model=list[ListingPublic]
)
async def get_user_listings(
    db: Annotated[Session, Depends(get_db)],
    user_id: uuid.UUID,
    params: Annotated[UserListingsParams, Depends()],
) -> list[Listing]:
    """
    Get all listings posted by a specific user.

    Args:
        db: Database session
        user_id: The user's unique identifier (UUID)
        params: Query parameters for filtering and pagination

    Returns:
        list[ListingPublic]: List of listings created by the user

    Raises:
        HTTPException: 404 if user not found, 500 on database error
    """
    return listing_service.get_by_seller(db, user_id, params)



@user_router.delete(
    "/{user_id}",
    summary="Delete a user",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_user(
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Delete the current user's account.

    Args:
        db: Database session
        current_user: The authenticated user (must not be banned)

    Returns:
        None

    Raises:
        HTTPException: 401 if not authenticated, 403 if banned, 500 on database error
    """
    return user_service.delete(db, current_user.id)
