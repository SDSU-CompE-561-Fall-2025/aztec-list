import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_not_banned
from app.core.rate_limiter import limiter
from app.models.profile import Profile
from app.models.user import User
from app.schemas.listing import (
    ListingSearchResponse,
    ListingSummary,
    UserListingsParams,
)
from app.schemas.profile import ProfilePublic
from app.schemas.user import PasswordChange, UserPublic, UserUpdate
from app.services.listing import listing_service
from app.services.profile import profile_service
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
    summary="Get a user's basic info",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get basic user info by ID.

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
    "/{user_id}/profile",
    summary="Get a user's public profile",
    status_code=status.HTTP_200_OK,
    response_model=ProfilePublic,
)
async def get_user_profile(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Get public profile for a specific user.

    This follows REST conventions where profile is a sub-resource of user.

    Args:
        user_id: The user's unique identifier (UUID)
        db: Database session

    Returns:
        ProfilePublic: User's profile information

    Raises:
        HTTPException: 404 if profile not found
    """
    return profile_service.get_by_user_id(db, user_id)


@user_router.get(
    "/{user_id}/listings", summary="Get user's listings", status_code=status.HTTP_200_OK
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
    listings, count = listing_service.get_by_seller(db, user_id, params)

    return ListingSearchResponse(
        items=[ListingSummary.model_validate(listing) for listing in listings],
        next_cursor=None,
        count=count,
    )


@user_router.patch(
    "/me",
    summary="Update current user",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
@limiter.limit("10/minute;30/hour")
async def update_current_user(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Update the current user's profile.

    Rate limit: 10 per minute (burst), 30 per hour (sustained).

    Args:
        request: FastAPI request object (required for rate limiting)
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


@user_router.patch(
    "/me/password",
    summary="Change current user password",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute;5/hour")
async def change_password(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """
    Change the current user's password.

    Rate limit: 3 per minute (burst), 5 per hour (sustained) - strict for security.

    Args:
        request: FastAPI request object (required for rate limiting)
        password_data: Current and new password
        current_user: The authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: 401 if current password is incorrect, 403 if banned
    """
    user_service.change_password(
        db,
        current_user.id,
        password_data.current_password,
        password_data.new_password,
    )
    return {"message": "Password changed successfully"}


@user_router.delete(
    "/me",
    summary="Delete current user",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
@limiter.limit("1/minute;2/hour")
async def delete_user(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Delete the current user's account.

    Rate limit: 1 per minute (burst), 2 per hour (sustained) - very strict for safety.

    Args:
        request: FastAPI request object (required for rate limiting)
        current_user: The authenticated user (must not be banned)
        db: Database session

    Returns:
        None

    Raises:
        HTTPException: 401 if not authenticated, 403 if banned, 500 on database error
    """
    return user_service.delete(db, current_user.id)
