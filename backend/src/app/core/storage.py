"""
File storage utilities.

This module provides utilities for handling file uploads and storage.
Images are organized by listing ID or user ID in subdirectories for easier management.
"""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.image_processing import strip_exif_and_optimize
from app.core.settings import settings

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Constants for path validation
MIN_PATH_PARTS = 5  # Updated: /, uploads, images, listing_id, filename
MIN_PROFILE_PATH_PARTS = 4  # /, uploads, profiles, user_id, filename


def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file.

    Checks file extension and MIME type to ensure it's a valid image.

    Args:
        file: Uploaded file to validate

    Raises:
        HTTPException: 400 if file validation fails
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.storage.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.storage.allowed_extensions)}",
        )

    if file.content_type not in settings.storage.allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"MIME type not allowed. Allowed types: {', '.join(settings.storage.allowed_mime_types)}",
        )


async def save_upload_file(file: UploadFile, listing_id: uuid.UUID) -> str:
    """
    Save uploaded file to disk with optimization.

    Files are organized by listing ID in subdirectories:
    uploads/images/{listing_id}/{filename}.jpg

    Args:
        file: Uploaded file to save
        listing_id: UUID of the listing this image belongs to

    Returns:
        str: URL path to the saved file (e.g., "/uploads/images/{listing_id}/uuid.jpg")

    Raises:
        HTTPException: 400 if file validation fails
        HTTPException: 413 if file is too large
        HTTPException: 500 if file save fails
    """
    validate_image_file(file)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size_bytes = settings.storage.max_file_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.storage.max_file_size_mb}MB",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    unique_filename = f"{uuid.uuid4()}.jpg"

    upload_path = Path(settings.storage.upload_dir) / str(listing_id)
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / unique_filename
    try:
        contents = await file.read()

        optimized_contents = strip_exif_and_optimize(contents)

        with file_path.open("wb") as f:
            f.write(optimized_contents)

        logger.info("Saved and optimized image: %s for listing %s", unique_filename, listing_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e!s}",
        ) from e

    return f"/uploads/images/{listing_id}/{unique_filename}"


async def save_profile_picture(file: UploadFile, user_id: uuid.UUID) -> str:
    """
    Save uploaded profile picture to disk with optimization.

    Profile pictures are stored in a user-specific directory:
    uploads/profiles/{user_id}/profile.jpg

    The old profile picture (if any) is automatically deleted before saving the new one.

    Args:
        file: Uploaded file to save
        user_id: UUID of the user

    Returns:
        str: URL path to the saved file (e.g., "/uploads/profiles/{user_id}/profile.jpg")

    Raises:
        HTTPException: 400 if file validation fails
        HTTPException: 413 if file is too large
        HTTPException: 500 if file save fails
    """
    validate_image_file(file)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size_bytes = settings.storage.max_file_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.storage.max_file_size_mb}MB",
        )

    # Use fixed filename to overwrite existing profile picture
    filename = "profile.jpg"
    upload_path = Path(settings.storage.profile_upload_dir) / str(user_id)
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / filename

    # Delete old profile picture if it exists
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info("Deleted old profile picture for user %s", user_id)
        except OSError as e:
            logger.warning("Failed to delete old profile picture: %s", e)

    try:
        contents = await file.read()
        optimized_contents = strip_exif_and_optimize(contents)

        with file_path.open("wb") as f:
            f.write(optimized_contents)

        logger.info("Saved and optimized profile picture for user %s", user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e!s}",
        ) from e

    return f"/uploads/profiles/{user_id}/{filename}"


def delete_profile_picture(user_id: uuid.UUID) -> None:
    """
    Delete profile picture for a user.

    Args:
        user_id: UUID of the user whose profile picture should be deleted

    Note:
        Does not raise an error if file doesn't exist (idempotent operation)
    """
    try:
        profile_path = Path(settings.storage.profile_upload_dir) / str(user_id) / "profile.jpg"

        if profile_path.exists() and profile_path.is_file():
            profile_path.unlink()
            logger.info("Deleted profile picture for user %s", user_id)
    except OSError as exc:
        logger.warning("Failed to delete profile picture for user %s: %s", user_id, exc)


def delete_file(url_path: str) -> None:
    """
    Delete a single file from disk.

    Extracts the filename from the URL path and removes the physical file.

    Args:
        url_path: URL path to the file (e.g., "/uploads/images/{listing_id}/uuid.jpg")

    Note:
        Does not raise an error if file doesn't exist (idempotent operation)
    """
    if not url_path:
        return

    try:
        # Extract path components from URL path
        # Expected format: /uploads/images/{listing_id}/uuid.jpg
        path_parts = Path(url_path).parts
        if (
            len(path_parts) >= MIN_PATH_PARTS
            and path_parts[1] == "uploads"
            and path_parts[2] == "images"
        ):
            listing_id = path_parts[3]
            filename = path_parts[4]
            file_path = Path(settings.storage.upload_dir) / listing_id / filename

            # Delete file if it exists
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info("Deleted file: %s", file_path)
    except (OSError, ValueError, IndexError) as exc:
        # Log deletion errors but don't break DB operations
        # Files can be cleaned up manually if needed
        logger.warning("Failed to delete file %s: %s", url_path, exc)


def delete_listing_images(listing_id: uuid.UUID) -> None:
    """
    Delete all images for a listing by removing its directory.

    This function removes the entire directory for a listing, which
    includes all images associated with that listing. This is more
    efficient than deleting files one by one and ensures complete cleanup.

    Args:
        listing_id: UUID of the listing whose images should be deleted

    Note:
        Does not raise an error if directory doesn't exist (idempotent operation)
    """
    try:
        listing_dir = Path(settings.storage.upload_dir) / str(listing_id)

        if listing_dir.exists() and listing_dir.is_dir():
            # Use shutil.rmtree to recursively delete directory and all contents
            shutil.rmtree(listing_dir)
            logger.info("Deleted all images for listing %s", listing_id)
        else:
            logger.debug("No image directory found for listing %s", listing_id)
    except OSError as exc:
        # Log deletion errors but don't break DB operations
        logger.warning("Failed to delete images for listing %s: %s", listing_id, exc)
