import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_not_banned
from app.models.listing import Listing
from app.models.user import User
from app.schemas.listing import ListingSearchResponse, ListingSummary, ListingPublic, UserListingsParams
from app.schemas.user import UserPublic, UserUpdate
from app.services.listing import listing_service
from app.services.user import user_service

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@user_router.get(
    "/me",
    summary="Get current user",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get the authenticated user's information.

    Args:
        current_user: The authenticated user from the JWT token
        db: Database session

    Returns:
        UserPublic: Current user's information

    Raises:
        HTTPException: 401 if not authenticated
    """
    return user_service.get_by_id(db, current_user.id)


@user_router.get(
    "/{user_id}",
    summary="Get a user's public profile",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
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
    "/{user_id}/listings",
    summary="Get user's listings",
    status_code=status.HTTP_200_OK,
    response_model=list[ListingPublic],
)
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
    return listing_service.get_by_seller(db, user_id, params)



@user_router.patch(
    "/me",
    summary="Update current user",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def update_current_user(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Update the current user's profile.

    Args:
        update_data: Fields to update
        current_user: The authenticated user
        db: Database session

    Returns:
        UserPublic: Updated user information

    Raises:
        HTTPException: 401 if not authenticated, 403 if banned
        HTTPException: 400 if username/email already taken
    """
    return user_service.update(db, current_user.id, update_data)


@user_router.delete(
    "/me",
    summary="Delete current user",
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
