"""
File storage utilities.

This module provides utilities for handling file uploads and storage.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.settings import settings

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Constants for path validation
MIN_PATH_PARTS = 4  # Minimum parts for valid upload path: /, uploads, images, filename


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

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.storage.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.storage.allowed_extensions)}",
        )

    # Check MIME type
    if file.content_type not in settings.storage.allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"MIME type not allowed. Allowed types: {', '.join(settings.storage.allowed_mime_types)}",
        )


async def save_upload_file(file: UploadFile) -> str:
    """
    Save uploaded file to disk.

    Generates a unique filename using UUID and saves the file to the configured
    upload directory. Returns the URL path that can be used to access the file.

    Args:
        file: File to save

    Returns:
        str: URL path to access the saved file (e.g., "/uploads/images/uuid.jpg")

    Raises:
        HTTPException: 400 if file validation fails
        HTTPException: 413 if file is too large
        HTTPException: 500 if file save fails
    """
    # Validate file
    validate_image_file(file)

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size_bytes = settings.storage.max_file_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.storage.max_file_size_mb}MB",
        )

    # Generate unique filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"

    # Create upload directory if it doesn't exist
    upload_path = Path(settings.storage.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = upload_path / unique_filename
    try:
        contents = await file.read()
        with file_path.open("wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e!s}",
        ) from e

    # Return URL path (not filesystem path)
    # Format: /uploads/images/uuid.jpg
    return f"/uploads/images/{unique_filename}"


def delete_file(url_path: str) -> None:
    """
    Delete a file from disk.

    Extracts the filename from the URL path and removes the physical file.

    Args:
        url_path: URL path to the file (e.g., "/uploads/images/uuid.jpg")

    Note:
        Does not raise an error if file doesn't exist (idempotent operation)
    """
    if not url_path:
        return

    try:
        # Extract filename from URL path
        # Expected format: /uploads/images/uuid.jpg
        path_parts = Path(url_path).parts
        if (
            len(path_parts) >= MIN_PATH_PARTS
            and path_parts[1] == "uploads"
            and path_parts[2] == "images"
        ):
            filename = path_parts[3]
            file_path = Path(settings.storage.upload_dir) / filename

            # Delete file if it exists
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info("Deleted file: %s", file_path)
    except (OSError, ValueError) as exc:
        # Log deletion errors but don't break DB operations
        # Files can be cleaned up manually if needed
        logger.warning("Failed to delete file %s: %s", url_path, exc)
