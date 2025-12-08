"""
File storage utilities.

This module provides utilities for handling file uploads and storage.
Images are organized by listing ID or user ID in subdirectories for easier management.

Integration with image_processing module:
- strip_exif_and_optimize() is called for all uploads to remove metadata and optimize images
- Image processor automatically determines if optimization is needed based on:
  * Format (preserves GIFs to maintain animation, optimizes PNGs)
  * Size (skips optimization for already-small JPEGs)
  * Dimensions (resizes images exceeding max width/height)
- File size validation is performed before processing to fail fast on oversized uploads
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

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


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


def validate_file_size(file: UploadFile, max_size_mb: int | None = None) -> int:
    """
    Validate file size and return file size in bytes.

    Args:
        file: Uploaded file to validate
        max_size_mb: Maximum file size in MB (uses settings if not provided)

    Returns:
        int: File size in bytes

    Raises:
        HTTPException: 413 if file is too large
    """
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size = max_size_mb or settings.storage.max_file_size_mb
    max_size_bytes = max_size * 1024 * 1024

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size}MB",
        )

    return file_size


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
    file_size = validate_file_size(file)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    try:
        contents = await file.read()
        # Image processor automatically strips EXIF and optimizes based on size/format
        # Returns both optimized bytes and the appropriate file extension
        optimized_contents, extension = strip_exif_and_optimize(contents)

        unique_filename = f"{uuid.uuid4()}{extension}"
        upload_path = Path(settings.storage.upload_dir) / str(listing_id)
        upload_path.mkdir(parents=True, exist_ok=True)
        file_path = upload_path / unique_filename

        file_path.write_bytes(optimized_contents)
        logger.info(
            "Saved and optimized listing image: %s (original: %d KB)",
            unique_filename,
            file_size // 1024,
        )
    except Exception as e:
        # Clean up partial file if save failed
        if file_path.exists():
            file_path.unlink(missing_ok=True)
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
    file_size = validate_file_size(file)

    try:
        contents = await file.read()
        # Image processor automatically preserves GIF/WEBP formats when appropriate
        # Returns both optimized bytes and the appropriate file extension
        optimized_contents, extension = strip_exif_and_optimize(contents)

        filename = f"profile{extension}"
        upload_path = Path(settings.storage.profile_upload_dir) / str(user_id)
        upload_path.mkdir(parents=True, exist_ok=True)
        file_path = upload_path / filename

        # Delete any old profile pictures with different extensions
        for old_file in upload_path.glob("profile.*"):
            if old_file != file_path:
                try:
                    old_file.unlink()
                    logger.info(
                        "Deleted old profile picture for user %s: %s", user_id, old_file.name
                    )
                except OSError as e:
                    logger.warning("Failed to delete old profile picture: %s", e)

        file_path.write_bytes(optimized_contents)
        logger.info(
            "Saved and optimized profile picture for user %s: %s (original: %d KB)",
            user_id,
            filename,
            file_size // 1024,
        )
    except Exception as e:
        # Clean up on failure
        if file_path.exists():
            file_path.unlink(missing_ok=True)
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
        Handles all supported image extensions
    """
    try:
        profile_dir = Path(settings.storage.profile_upload_dir) / str(user_id)

        # Delete all profile pictures with any extension
        for profile_file in profile_dir.glob("profile.*"):
            if profile_file.is_file():
                profile_file.unlink()
                logger.info("Deleted profile picture for user %s: %s", user_id, profile_file.name)
    except OSError as exc:
        logger.warning("Failed to delete profile picture for user %s: %s", user_id, exc)


def delete_file(url_path: str) -> None:
    """
    Delete a single file from disk.

    Extracts the filename from the URL path and removes the physical file.
    Expected URL format: /uploads/images/{listing_id}/{filename}

    Args:
        url_path: URL path to the file (e.g., "/uploads/images/{listing_id}/uuid.jpg")

    Note:
        Does not raise errors - logs warnings instead to avoid breaking DB operations
        Returns early if path is invalid or doesn't match expected format
    """
    if not url_path:
        return

    try:
        # Extract path components from URL path
        path_parts = Path(url_path).parts

        # Validate path structure: /uploads/images/{listing_id}/{filename}
        if len(path_parts) < MIN_PATH_PARTS:
            logger.debug("Path too short: %s", url_path)
            return

        if path_parts[1] != "uploads" or path_parts[2] != "images":
            logger.debug("Invalid path format: %s", url_path)
            return

        listing_id = path_parts[3]
        filename = path_parts[4]
        file_path = Path(settings.storage.upload_dir) / listing_id / filename

        # Delete file if it exists
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info("Deleted file: %s", file_path)
        else:
            logger.debug("File not found: %s", file_path)

    except (OSError, ValueError, IndexError) as exc:
        # Log deletion errors but don't break DB operations
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
