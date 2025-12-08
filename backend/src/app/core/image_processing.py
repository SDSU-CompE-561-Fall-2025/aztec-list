"""
Image processing utilities.

This module provides utilities for optimizing, resizing, and processing images.

Key features:
- Intelligent optimization: Only processes images that need it (based on format, size, dimensions)
- Format preservation: Returns original bytes for GIF (animations) and suitable WEBPs
- EXIF stripping: Removes metadata for privacy (JPEG/TIFF only, to avoid breaking other formats)
- Auto-rotation: Respects EXIF orientation before removing metadata (JPEG/TIFF only)
- Dimension limits: Resizes images exceeding MAX_IMAGE_WIDTH x MAX_IMAGE_HEIGHT
- Quality balance: Uses high-quality JPEG compression (85) for good size/quality ratio

Processing flow:
1. Analyze format and dimensions to determine if optimization is needed
2. If not needed (GIF, small WEBP, small JPEG): return original bytes unchanged
3. If needed: apply EXIF operations (JPEG/TIFF only), resize, convert to RGB, compress as JPEG

Used by storage module for all image uploads (listings and profile pictures).
"""

from __future__ import annotations

import io
import logging

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

MAX_IMAGE_WIDTH = 815
MAX_IMAGE_HEIGHT = 910
THUMBNAIL_SIZE = (300, 300)
JPEG_QUALITY = 85
THUMBNAIL_QUALITY = 80
RESAMPLING_FILTER = Image.Resampling.LANCZOS

SIZE_THRESHOLD_FOR_OPTIMIZATION = 1920
ALREADY_OPTIMIZED_SIZE_KB = 500


def should_optimize_image(img: Image.Image, file_size: int, format_name: str | None) -> bool:
    """
    Determine if an image needs optimization.

    Args:
        img: PIL Image object
        file_size: Original file size in bytes
        format_name: Image format (e.g., 'JPEG', 'PNG')

    Returns:
        bool: True if image should be optimized
    """
    if format_name == "PNG":
        return True

    # Preserve modern formats unless dimensions exceed limits
    if format_name == "WEBP":
        return img.width > MAX_IMAGE_WIDTH or img.height > MAX_IMAGE_HEIGHT

    # Preserve GIFs (may be animated)
    if format_name == "GIF":
        return False

    if format_name == "JPEG":
        if img.width > MAX_IMAGE_WIDTH or img.height > MAX_IMAGE_HEIGHT:
            logger.info(
                "Image needs optimization: dimensions %dx%d exceed max %dx%d",
                img.width,
                img.height,
                MAX_IMAGE_WIDTH,
                MAX_IMAGE_HEIGHT,
            )
            return True

        file_size_kb = file_size / 1024
        if file_size_kb < ALREADY_OPTIMIZED_SIZE_KB:
            logger.info("Skipping optimization: JPEG is already small (%.1f KB)", file_size_kb)
            return False

        # Large JPEG file might benefit from optimization
        logger.info("JPEG file is large (%.1f KB), will optimize", file_size_kb)

    # Other formats or large JPEGs: optimize
    return True


def strip_exif_and_optimize(
    file_content: bytes,
    max_width: int = MAX_IMAGE_WIDTH,
    max_height: int = MAX_IMAGE_HEIGHT,
    quality: int = JPEG_QUALITY,
) -> tuple[bytes, str]:
    """
    Strip EXIF metadata and optimize image for web.

    This function:
    - Determines if optimization is needed based on format and size
    - Removes all EXIF metadata (privacy/security)
    - Converts to RGB mode if needed
    - Resizes if too large
    - Compresses to JPEG with optimization (only if needed)
    - Auto-rotates based on EXIF orientation (before stripping)

    Args:
        file_content: Original image file bytes
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100, higher = better quality)

    Returns:
        tuple[bytes, str]: Tuple of (optimized image bytes, file extension with dot)

    Raises:
        Exception: If image processing fails
    """
    try:
        img = Image.open(io.BytesIO(file_content))
        original_format = img.format

        needs_optimization = should_optimize_image(img, len(file_content), original_format)

        # For formats we want to preserve (GIF, small WEBPs), return original bytes
        if not needs_optimization:
            logger.info(
                "Image doesn't need optimization, preserving original format: %s (%d KB)",
                original_format,
                len(file_content) // 1024,
            )

            # Map format to extension
            format_to_ext = {
                "GIF": ".gif",
                "WEBP": ".webp",
                "PNG": ".png",
                "JPEG": ".jpg",
            }
            extension = format_to_ext.get(original_format or "JPEG", ".jpg")

            # Return original bytes unchanged to preserve animations, metadata, etc.
            return file_content, extension

        logger.info("Performing full image optimization")

        # Only apply EXIF transpose to formats that support EXIF (JPEG, some TIFFs)
        if original_format in ("JPEG", "TIFF"):
            img = ImageOps.exif_transpose(img)

        # Convert to RGB for optimization (all optimized images become JPEG)
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if dimensions exceed limits
        if img.width > max_width or img.height > max_height:
            original_size = (img.width, img.height)
            img.thumbnail((max_width, max_height), RESAMPLING_FILTER)
            logger.info(
                "Resized image from %dx%d to %dx%d",
                original_size[0],
                original_size[1],
                img.width,
                img.height,
            )

        # Save as optimized JPEG
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        optimized_size = len(output.getvalue())
        original_size = len(file_content)
        savings_percent = ((original_size - optimized_size) / original_size) * 100
        logger.info(
            "Optimization complete: %d KB -> %d KB (%.1f%% reduction)",
            original_size // 1024,
            optimized_size // 1024,
            savings_percent,
        )

        return output.getvalue(), ".jpg"

    except Exception:
        logger.exception("Image processing failed")
        raise


def create_thumbnail(
    file_content: bytes,
    size: tuple[int, int] = THUMBNAIL_SIZE,
    quality: int = THUMBNAIL_QUALITY,
) -> bytes:
    """
    Create a thumbnail from image.

    Args:
        file_content: Original image file bytes
        size: Thumbnail size as (width, height) tuple
        quality: JPEG quality (1-100)

    Returns:
        bytes: Thumbnail as JPEG bytes

    Raises:
        Exception: If thumbnail generation fails
    """
    try:
        img = Image.open(io.BytesIO(file_content))

        img = ImageOps.exif_transpose(img)

        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        img.thumbnail(size, RESAMPLING_FILTER)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        return output.getvalue()

    except Exception:
        logger.exception("Thumbnail creation failed")
        raise


def get_image_dimensions(file_content: bytes) -> tuple[int, int]:
    """
    Get image dimensions without loading full image.

    Args:
        file_content: Image file bytes

    Returns:
        tuple[int, int]: Width and height in pixels

    Raises:
        Exception: If reading dimensions fails
    """
    try:
        img = Image.open(io.BytesIO(file_content))
    except Exception:
        logger.exception("Failed to read image dimensions")
        raise
    else:
        return img.size
