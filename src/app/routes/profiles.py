from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_not_banned
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import (
    ProfileCreate,
    ProfilePictureResponse,
    ProfilePictureUpdate,
    ProfilePublic,
    ProfileUpdate,
)
from app.services.profile import profile_service

profile_router = APIRouter(
    prefix="/users/profile",
    tags=["Profile"],
)


@profile_router.post(
    "/",
    summary="Create a profile for the authenticated user",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfilePublic,
)
async def create_profile(
    profile: ProfileCreate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Create a user profile for the authenticated user after signup.

    Args:
        profile: Profile creation data (name, campus, contact_info)
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePublic: Created profile information

    Raises:
        HTTPException: 400 if profile already exists, 401 if not authenticated, 403 if banned
    """
    return profile_service.create(db, current_user.id, profile)


@profile_router.get(
    "/", summary="Get the authenticated user's profile", response_model=ProfilePublic
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Retrieve the authenticated user's full profile.

    Args:
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePublic: User's profile information

    Raises:
        HTTPException: 401 if not authenticated, 404 if profile not found
    """
    return profile_service.get_by_user_id(db, current_user.id)


@profile_router.patch(
    "/", summary="Update the authenticated user's profile", response_model=ProfilePublic
)
async def update_profile(
    profile: ProfileUpdate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Update fields of the authenticated user's profile.

    All fields are optional; only provided ones are updated.

    Args:
        profile: Profile update data (name, campus, contact_info)
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePublic: Updated profile information

    Raises:
        HTTPException: 401 if not authenticated, 403 if banned, 404 if profile not found
    """
    return profile_service.update(db, current_user.id, profile)


@profile_router.post(
    "/picture",
    summary="Upload/replace profile picture",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfilePictureResponse,
)
async def update_profile_picture(
    data: ProfilePictureUpdate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Upload or replace the user's profile picture.

    Note: This is a simplified version that accepts a URL string.
    For actual file upload, use multipart/form-data with File upload.

    Args:
        data: Profile picture update data with validated URL
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePictureResponse: Updated profile picture information

    Raises:
        HTTPException: 401 if not authenticated, 403 if banned, 404 if profile not found, 422 if invalid URL format
    """
    return profile_service.update_profile_picture(db, current_user.id, data)
