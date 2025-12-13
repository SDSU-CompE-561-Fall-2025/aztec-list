from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_not_banned
from app.core.rate_limiter import limiter
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import (
    ProfileCreate,
    ProfilePictureResponse,
    ProfilePictureUpdate,
    ProfilePrivate,
    ProfileUpdate,
)
from app.services.profile import profile_service

profile_router = APIRouter(
    prefix="/users/profile",
    tags=["Profile"],
    # Note: Public profiles are accessed via /users/{user_id}/profile in users router
)


@profile_router.post(
    "",
    summary="Create a profile for the authenticated user",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfilePrivate,
)
async def create_profile(
    profile: ProfileCreate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Create a user profile for the authenticated user.

    This endpoint is for authenticated users to create their own profile.
    Public profiles are accessed via GET /users/{user_id}/profile.

    Args:
        profile: Profile creation data (name, campus, contact_info)
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePrivate: Created profile information with contact info

    Raises:
        HTTPException: 400 if profile already exists, 401 if not authenticated, 403 if banned
    """
    return profile_service.create(db, current_user.id, profile)


@profile_router.get(
    "", summary="Get the authenticated user's profile", response_model=ProfilePrivate
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Retrieve the authenticated user's own profile.

    For viewing other users' public profiles, use GET /users/{user_id}/profile.

    Args:
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePrivate: User's profile information with contact info

    Raises:
        HTTPException: 401 if not authenticated, 404 if profile not found
    """
    return profile_service.get_by_user_id(db, current_user.id)


@profile_router.patch(
    "", summary="Update the authenticated user's profile", response_model=ProfilePrivate
)
@limiter.limit("10/minute;30/hour")
async def update_profile(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    profile: ProfileUpdate,
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> Profile:
    """
    Update fields of the authenticated user's own profile.

    Rate limit: 10 per minute (burst), 30 per hour (sustained).

    All fields are optional; only provided ones are updated.
    This endpoint is for authenticated users to update their own profile.

    Args:
        request: FastAPI request object (required for rate limiting)
        profile: Profile update data (name, campus, contact_info)
        current_user: Authenticated user from the JWT token
        db: Database session

    Returns:
        ProfilePrivate: Updated profile information with contact info

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
@limiter.limit("5/minute;20/hour")
async def update_profile_picture(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile | None, File(description="Profile picture file")] = None,
    picture_url: Annotated[str | None, Form(description="Profile picture URL")] = None,
) -> Profile:
    """
    Upload or replace the authenticated user's profile picture.

    Rate limit: 5 per minute (burst), 20 per hour (sustained).

    Accepts either:
    - File upload (multipart/form-data with 'file' field) - recommended
    - URL string (form field 'picture_url') - for external images

    Only one method should be provided. File upload takes precedence if both are provided.

    Args:
        request: FastAPI request object (required for rate limiting)
        current_user: Authenticated user from the JWT token
        db: Database session
        file: Image file to upload (jpg, png, webp, gif - max 5MB)
        picture_url: URL to an external image (if not uploading file)

    Returns:
        ProfilePictureResponse: Updated profile picture information

    Raises:
        HTTPException: 400 if neither file nor URL provided or validation fails
        HTTPException: 401 if not authenticated
        HTTPException: 403 if banned
        HTTPException: 404 if profile not found
        HTTPException: 413 if file too large
        HTTPException: 415 if unsupported file type
    """
    # Prioritize file upload over URL
    if file:
        return await profile_service.upload_profile_picture(db, current_user.id, file)

    if picture_url:
        # Use URL method (existing functionality)
        try:
            validated_url = HttpUrl(picture_url)
            data = ProfilePictureUpdate(picture_url=validated_url)
            return profile_service.update_profile_picture(db, current_user.id, data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL format: {e!s}",
            ) from e

    # Neither file nor URL provided
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either 'file' or 'picture_url' must be provided",
    )


@profile_router.delete(
    "",
    summary="Delete a user profile",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
@limiter.limit("1/minute;2/hour")
async def delete_profile(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    current_user: Annotated[User, Depends(require_not_banned)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Delete the authenticated user's own profile.

    Rate limit: 1 per minute (burst), 2 per hour (sustained) - very strict for safety.

    This endpoint is for authenticated users to delete their own profile.

    Args:
        request: FastAPI request object (required for rate limiting)
        current_user: Authenticated user from the JWT token (must not be banned)
        db: Database session

    Returns:
        None

    Raises:
        HTTPException: 401 if not authenticated, 403 if banned, 404 if profile not found, 500 on database error
    """
    return profile_service.delete(db, current_user.id)
