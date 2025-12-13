"""Unit tests for storage utilities."""

import io
import logging
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.core.storage import (
    delete_file,
    delete_listing_images,
    delete_profile_picture,
    save_profile_picture,
    save_upload_file,
    validate_file_size,
    validate_image_file,
)


class TestValidateImageFile:
    """Tests for validate_image_file."""

    @patch("app.core.storage.settings")
    def test_missing_filename_raises_error(self, mock_settings):
        """Test that missing filename raises 400 error."""
        file = UploadFile(file=io.BytesIO(), filename=None)

        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)

        assert exc_info.value.status_code == 400
        assert "Filename is required" in exc_info.value.detail

    @patch("app.core.storage.settings")
    def test_invalid_extension_raises_error(self, mock_settings):
        """Test that invalid file extension raises 400 error."""
        mock_settings.storage.allowed_extensions = {".jpg", ".png"}

        file = UploadFile(file=io.BytesIO(), filename="test.txt")

        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)

        assert exc_info.value.status_code == 400
        assert "File type not allowed" in exc_info.value.detail

    @patch("app.core.storage.settings")
    def test_invalid_mime_type_raises_error(self, mock_settings):
        """Test that invalid MIME type raises 415 error."""
        mock_settings.storage.allowed_extensions = {".jpg", ".png"}
        mock_settings.storage.allowed_mime_types = {"image/jpeg", "image/png"}

        headers = Headers({"content-type": "text/plain"})
        file = UploadFile(file=io.BytesIO(), filename="test.jpg", headers=headers)

        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)

        assert exc_info.value.status_code == 415
        assert "MIME type not allowed" in exc_info.value.detail

    @patch("app.core.storage.settings")
    def test_valid_file_passes(self, mock_settings):
        """Test that valid file passes validation."""
        mock_settings.storage.allowed_extensions = {".jpg", ".png"}
        mock_settings.storage.allowed_mime_types = {"image/jpeg", "image/png"}

        headers = Headers({"content-type": "image/jpeg"})
        file = UploadFile(file=io.BytesIO(), filename="test.jpg", headers=headers)

        # Should not raise
        validate_image_file(file)


class TestValidateFileSize:
    """Tests for validate_file_size."""

    @patch("app.core.storage.settings")
    def test_file_too_large_raises_error(self, mock_settings):
        """Test that oversized file raises 413 error."""
        mock_settings.storage.max_file_size_mb = 5

        # Create file with 6MB of data
        file_data = b"x" * (6 * 1024 * 1024)
        file = UploadFile(filename="test.jpg", file=io.BytesIO(file_data))

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(file)

        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail

    @patch("app.core.storage.settings")
    def test_file_within_limit_returns_size(self, mock_settings):
        """Test that file within limit returns file size."""
        mock_settings.storage.max_file_size_mb = 5

        # Create file with 3MB of data
        file_data = b"x" * (3 * 1024 * 1024)
        file = UploadFile(filename="test.jpg", file=io.BytesIO(file_data))

        size = validate_file_size(file)

        assert size == 3 * 1024 * 1024

    @patch("app.core.storage.settings")
    def test_custom_max_size(self, mock_settings):
        """Test that custom max size overrides settings."""
        mock_settings.storage.max_file_size_mb = 5

        # Create file with 3MB of data
        file_data = b"x" * (3 * 1024 * 1024)
        file = UploadFile(filename="test.jpg", file=io.BytesIO(file_data))

        # Use custom max of 2MB - should fail
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(file, max_size_mb=2)

        assert exc_info.value.status_code == 413


class TestSaveUploadFile:
    """Tests for save_upload_file."""

    @pytest.mark.asyncio
    @patch("app.core.storage.strip_exif_and_optimize")
    @patch("app.core.storage.settings")
    @patch("app.core.storage.validate_file_size")
    @patch("app.core.storage.validate_image_file")
    async def test_successful_save(
        self, mock_validate_image, mock_validate_size, mock_settings, mock_optimize
    ):
        """Test successful file save with optimization."""
        mock_settings.storage.upload_dir = "uploads/images"
        mock_settings.storage.allowed_extensions = {".jpg"}
        mock_settings.storage.allowed_mime_types = {"image/jpeg"}
        mock_validate_size.return_value = 1024 * 100  # 100KB

        listing_id = uuid.uuid4()
        file_data = b"fake image data"
        file = UploadFile(filename="test.jpg", file=io.BytesIO(file_data))

        # Mock optimization returning different bytes and extension
        mock_optimize.return_value = (b"optimized data", ".jpg")

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes") as mock_write:
            result = await save_upload_file(file, listing_id)

        # Verify optimization was called
        mock_optimize.assert_called_once_with(file_data)

        # Verify file was written with optimized data
        mock_write.assert_called_once_with(b"optimized data")

        # Verify URL format
        assert result.startswith(f"/uploads/images/{listing_id}/")
        assert result.endswith(".jpg")

    @pytest.mark.asyncio
    @patch("app.core.storage.settings")
    @patch("app.core.storage.validate_file_size")
    @patch("app.core.storage.validate_image_file")
    async def test_missing_filename_raises_error(
        self, mock_validate_image, mock_validate_size, mock_settings
    ):
        """Test that missing filename raises error."""
        listing_id = uuid.uuid4()
        file = UploadFile(file=io.BytesIO(), filename=None)

        with pytest.raises(HTTPException) as exc_info:
            await save_upload_file(file, listing_id)

        assert exc_info.value.status_code == 400
        assert "Filename is required" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.core.storage.strip_exif_and_optimize")
    @patch("app.core.storage.settings")
    @patch("app.core.storage.validate_file_size")
    @patch("app.core.storage.validate_image_file")
    async def test_save_failure_cleanup(
        self, mock_validate_image, mock_validate_size, mock_settings, mock_optimize
    ):
        """Test that file is cleaned up on save failure."""
        mock_settings.storage.upload_dir = "uploads/images"
        mock_validate_size.return_value = 1024 * 100

        listing_id = uuid.uuid4()
        file_data = b"fake image data"
        file = UploadFile(filename="test.jpg", file=io.BytesIO(file_data))

        mock_optimize.return_value = (b"optimized data", ".jpg")

        # Mock write_bytes to raise an exception
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_bytes", side_effect=OSError("Disk full")),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink") as mock_unlink,
            pytest.raises(HTTPException) as exc_info,
        ):
            await save_upload_file(file, listing_id)

        # Verify cleanup was attempted
        mock_unlink.assert_called_once()
        assert exc_info.value.status_code == 500
        assert "Failed to save file" in exc_info.value.detail


class TestSaveProfilePicture:
    """Tests for save_profile_picture."""

    @pytest.mark.asyncio
    @patch("app.core.storage.strip_exif_and_optimize")
    @patch("app.core.storage.settings")
    @patch("app.core.storage.validate_file_size")
    @patch("app.core.storage.validate_image_file")
    async def test_successful_save(
        self, mock_validate_image, mock_validate_size, mock_settings, mock_optimize
    ):
        """Test successful profile picture save."""
        mock_settings.storage.profile_upload_dir = "uploads/profiles"
        mock_validate_size.return_value = 1024 * 50  # 50KB

        user_id = uuid.uuid4()
        file_data = b"fake image data"
        file = UploadFile(filename="profile.jpg", file=io.BytesIO(file_data))

        mock_optimize.return_value = (b"optimized data", ".jpg")

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_bytes") as mock_write,
            patch("pathlib.Path.glob", return_value=[]),  # No old files
        ):
            result = await save_profile_picture(file, user_id)

        mock_optimize.assert_called_once_with(file_data)
        mock_write.assert_called_once_with(b"optimized data")
        assert result == f"/uploads/profiles/{user_id}/profile.jpg"

    @pytest.mark.asyncio
    @patch("app.core.storage.strip_exif_and_optimize")
    @patch("app.core.storage.settings")
    @patch("app.core.storage.validate_file_size")
    @patch("app.core.storage.validate_image_file")
    async def test_deletes_old_profile_pictures(
        self, mock_validate_image, mock_validate_size, mock_settings, mock_optimize
    ):
        """Test that old profile pictures are deleted."""
        mock_settings.storage.profile_upload_dir = "uploads/profiles"
        mock_validate_size.return_value = 1024 * 50

        user_id = uuid.uuid4()
        file_data = b"fake image data"
        file = UploadFile(filename="profile.png", file=io.BytesIO(file_data))

        # Mock returns PNG extension
        mock_optimize.return_value = (b"optimized data", ".png")

        # Mock old profile.jpg exists
        old_file = MagicMock(spec=Path)
        old_file.name = "profile.jpg"
        old_file.__eq__ = lambda self, other: False  # Not equal to new file

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_bytes"),
            patch("pathlib.Path.glob", return_value=[old_file]),
        ):
            result = await save_profile_picture(file, user_id)

        # Verify old file was deleted
        old_file.unlink.assert_called_once()
        assert result == f"/uploads/profiles/{user_id}/profile.png"

    @pytest.mark.asyncio
    @patch("app.core.storage.strip_exif_and_optimize")
    @patch("app.core.storage.settings")
    @patch("app.core.storage.validate_file_size")
    @patch("app.core.storage.validate_image_file")
    async def test_save_failure_cleanup(
        self, mock_validate_image, mock_validate_size, mock_settings, mock_optimize
    ):
        """Test cleanup on save failure."""
        mock_settings.storage.profile_upload_dir = "uploads/profiles"
        mock_validate_size.return_value = 1024 * 50

        user_id = uuid.uuid4()
        file = UploadFile(filename="profile.jpg", file=io.BytesIO(b"data"))

        mock_optimize.return_value = (b"optimized data", ".jpg")

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_bytes", side_effect=OSError("Disk error")),
            patch("pathlib.Path.glob", return_value=[]),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink") as mock_unlink,
            pytest.raises(HTTPException) as exc_info,
        ):
            await save_profile_picture(file, user_id)

        mock_unlink.assert_called_once()
        assert exc_info.value.status_code == 500


class TestDeleteProfilePicture:
    """Tests for delete_profile_picture."""

    @patch("app.core.storage.settings")
    def test_deletes_profile_pictures(self, mock_settings):
        """Test successful deletion of profile pictures."""
        mock_settings.storage.profile_upload_dir = "uploads/profiles"

        user_id = uuid.uuid4()

        # Mock profile files
        file1 = MagicMock(spec=Path)
        file1.is_file.return_value = True
        file1.name = "profile.jpg"

        file2 = MagicMock(spec=Path)
        file2.is_file.return_value = True
        file2.name = "profile.png"

        with patch("pathlib.Path.glob", return_value=[file1, file2]):
            delete_profile_picture(user_id)

        file1.unlink.assert_called_once()
        file2.unlink.assert_called_once()

    @patch("app.core.storage.settings")
    def test_no_files_no_error(self, mock_settings):
        """Test that no files doesn't raise error."""
        mock_settings.storage.profile_upload_dir = "uploads/profiles"

        user_id = uuid.uuid4()

        with patch("pathlib.Path.glob", return_value=[]):
            # Should not raise
            delete_profile_picture(user_id)

    @patch("app.core.storage.settings")
    def test_deletion_error_logged(self, mock_settings, caplog):
        """Test that deletion errors are logged, not raised."""
        mock_settings.storage.profile_upload_dir = "uploads/profiles"

        user_id = uuid.uuid4()

        file1 = MagicMock(spec=Path)
        file1.is_file.return_value = True
        file1.unlink.side_effect = OSError("Permission denied")
        file1.name = "profile.jpg"

        with (
            patch("pathlib.Path.glob", return_value=[file1]),
            caplog.at_level(logging.WARNING),
        ):
            # Should not raise
            delete_profile_picture(user_id)

        assert "Failed to delete profile picture" in caplog.text


class TestDeleteFile:
    """Tests for delete_file."""

    @patch("app.core.storage.settings")
    def test_deletes_valid_file(self, mock_settings):
        """Test successful file deletion."""
        mock_settings.storage.upload_dir = "uploads/images"

        listing_id = uuid.uuid4()
        url_path = f"/uploads/images/{listing_id}/test.jpg"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.unlink") as mock_unlink,
        ):
            delete_file(url_path)

        mock_unlink.assert_called_once()

    @patch("app.core.storage.settings")
    def test_empty_path_returns_early(self, mock_settings):
        """Test that empty path returns without error."""
        with patch("pathlib.Path.unlink") as mock_unlink:
            delete_file("")

        mock_unlink.assert_not_called()

    @patch("app.core.storage.settings")
    def test_invalid_path_structure_returns_early(self, mock_settings):
        """Test that invalid path structure returns early."""
        with patch("pathlib.Path.unlink") as mock_unlink:
            delete_file("/uploads/invalid.jpg")  # Too short

        mock_unlink.assert_not_called()

    @patch("app.core.storage.settings")
    def test_wrong_directory_returns_early(self, mock_settings):
        """Test that wrong directory path returns early."""
        listing_id = uuid.uuid4()

        with patch("pathlib.Path.unlink") as mock_unlink:
            delete_file(f"/wrong/dir/{listing_id}/test.jpg")

        mock_unlink.assert_not_called()

    @patch("app.core.storage.settings")
    def test_file_not_found_no_error(self, mock_settings):
        """Test that non-existent file doesn't raise error."""
        mock_settings.storage.upload_dir = "uploads/images"

        listing_id = uuid.uuid4()
        url_path = f"/uploads/images/{listing_id}/test.jpg"

        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.unlink") as mock_unlink,
        ):
            delete_file(url_path)

        mock_unlink.assert_not_called()

    @patch("app.core.storage.settings")
    def test_deletion_error_logged(self, mock_settings, caplog):
        """Test that deletion errors are logged."""
        mock_settings.storage.upload_dir = "uploads/images"

        listing_id = uuid.uuid4()
        url_path = f"/uploads/images/{listing_id}/test.jpg"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")),
            caplog.at_level(logging.WARNING),
        ):
            # Should not raise
            delete_file(url_path)

        assert "Failed to delete file" in caplog.text


class TestDeleteListingImages:
    """Tests for delete_listing_images."""

    @patch("app.core.storage.shutil")
    @patch("app.core.storage.settings")
    def test_deletes_listing_directory(self, mock_settings, mock_shutil):
        """Test successful deletion of listing directory."""
        mock_settings.storage.upload_dir = "uploads/images"

        listing_id = uuid.uuid4()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
        ):
            delete_listing_images(listing_id)

        # Verify shutil.rmtree was called
        mock_shutil.rmtree.assert_called_once()

    @patch("app.core.storage.shutil")
    @patch("app.core.storage.settings")
    def test_no_directory_no_error(self, mock_settings, mock_shutil):
        """Test that non-existent directory doesn't raise error."""
        mock_settings.storage.upload_dir = "uploads/images"

        listing_id = uuid.uuid4()

        with patch("pathlib.Path.exists", return_value=False):
            delete_listing_images(listing_id)

        mock_shutil.rmtree.assert_not_called()

    @patch("app.core.storage.shutil")
    @patch("app.core.storage.settings")
    def test_deletion_error_logged(self, mock_settings, mock_shutil, caplog):
        """Test that deletion errors are logged."""
        mock_settings.storage.upload_dir = "uploads/images"

        listing_id = uuid.uuid4()

        mock_shutil.rmtree.side_effect = OSError("Permission denied")

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            caplog.at_level(logging.WARNING),
        ):
            # Should not raise
            delete_listing_images(listing_id)

        assert "Failed to delete images" in caplog.text
