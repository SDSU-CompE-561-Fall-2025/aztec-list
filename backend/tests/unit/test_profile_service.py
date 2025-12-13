"""
Unit tests for ProfileService.

Tests the business logic layer for profile operations.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfilePictureUpdate, ProfileUpdate
from app.services.profile import ProfileService


@pytest.fixture
def profile_service():
    """Create ProfileService instance."""
    return ProfileService()


@pytest.fixture
def mock_profile():
    """Create a mock profile."""
    return Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="John Doe",
        campus="UC San Diego",
        contact_info={"email": "john@example.edu"},
    )


class TestProfileServiceGet:
    """Test ProfileService get methods."""

    def test_get_by_user_id_success(self, profile_service: ProfileService, mock_profile: Profile):
        """Test getting profile by user ID when exists."""
        with patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get:
            mock_get.return_value = mock_profile
            db = MagicMock(spec=Session)

            result = profile_service.get_by_user_id(db, mock_profile.user_id)

            assert result == mock_profile
            mock_get.assert_called_once_with(db, mock_profile.user_id)

    def test_get_by_user_id_not_found_raises_404(self, profile_service: ProfileService):
        """Test getting profile by user ID when doesn't exist raises 404."""
        with patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                profile_service.get_by_user_id(db, uuid.uuid4())

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_by_id_success(self, profile_service: ProfileService, mock_profile: Profile):
        """Test getting profile by ID when exists."""
        with patch("app.services.profile.ProfileRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_profile
            db = MagicMock(spec=Session)

            result = profile_service.get_by_id(db, mock_profile.id)

            assert result == mock_profile

    def test_get_by_id_not_found_raises_404(self, profile_service: ProfileService):
        """Test getting profile by ID when doesn't exist raises 404."""
        with patch("app.services.profile.ProfileRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            profile_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                profile_service.get_by_id(db, profile_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(profile_id) in exc_info.value.detail


class TestProfileServiceCreate:
    """Test ProfileService create method."""

    def test_create_profile_success(self, profile_service: ProfileService, mock_profile: Profile):
        """Test creating a new profile successfully."""
        profile_data = ProfileCreate(
            name="John Doe",
            campus="UC San Diego",
            contact_info={"email": "john@example.edu"},
        )

        with (
            patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get,
            patch("app.services.profile.ProfileRepository.create") as mock_create,
        ):
            mock_get.return_value = None  # No existing profile
            mock_create.return_value = mock_profile
            db = MagicMock(spec=Session)

            result = profile_service.create(db, mock_profile.user_id, profile_data)

            assert result == mock_profile
            mock_create.assert_called_once()

    def test_create_profile_already_exists_raises_400(
        self, profile_service: ProfileService, mock_profile: Profile
    ):
        """Test creating profile when one already exists raises 400."""
        profile_data = ProfileCreate(
            name="John Doe",
            campus="UC San Diego",
        )

        with patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get:
            mock_get.return_value = mock_profile  # Profile already exists
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                profile_service.create(db, mock_profile.user_id, profile_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "already exists" in exc_info.value.detail.lower()


class TestProfileServiceUpdate:
    """Test ProfileService update method."""

    def test_update_profile_success(self, profile_service: ProfileService, mock_profile: Profile):
        """Test updating profile successfully."""
        update_data = ProfileUpdate(name="Jane Doe")

        with (
            patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get,
            patch("app.services.profile.ProfileRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_profile
            # Just return the same profile since we're mocking
            mock_update.return_value = mock_profile
            db = MagicMock(spec=Session)

            result = profile_service.update(db, mock_profile.user_id, update_data)

            assert result == mock_profile
            mock_update.assert_called_once()

    def test_update_profile_not_found_raises_404(self, profile_service: ProfileService):
        """Test updating non-existent profile creates it (upsert)."""
        update_data = ProfileUpdate(name="New Name")
        new_profile = Profile(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="New Name",
        )

        with (
            patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get,
            patch("app.services.profile.ProfileRepository.create") as mock_create,
        ):
            mock_get.return_value = None
            mock_create.return_value = new_profile
            db = MagicMock(spec=Session)

            result = profile_service.update(db, new_profile.user_id, update_data)

            assert result == new_profile
            mock_create.assert_called_once()

    def test_update_profile_picture_success(
        self, profile_service: ProfileService, mock_profile: Profile
    ):
        """Test updating profile picture successfully."""
        picture_data = ProfilePictureUpdate(picture_url="https://example.com/pic.jpg")

        with (
            patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get,
            patch("app.services.profile.ProfileRepository.update_profile_picture") as mock_update,
        ):
            mock_get.return_value = mock_profile
            mock_update.return_value = mock_profile
            db = MagicMock(spec=Session)

            result = profile_service.update_profile_picture(db, mock_profile.user_id, picture_data)

            assert result == mock_profile
            mock_update.assert_called_once()

    def test_update_profile_picture_not_found_raises_404(self, profile_service: ProfileService):
        """Test updating profile picture when profile doesn't exist creates it."""
        picture_data = ProfilePictureUpdate(picture_url="https://example.com/pic.jpg")
        new_profile = Profile(id=uuid.uuid4(), user_id=uuid.uuid4())

        with (
            patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get,
            patch("app.services.profile.ProfileRepository.create") as mock_create,
            patch("app.services.profile.ProfileRepository.update_profile_picture") as mock_update,
        ):
            mock_get.return_value = None
            mock_create.return_value = new_profile
            mock_update.return_value = new_profile
            db = MagicMock(spec=Session)

            result = profile_service.update_profile_picture(db, new_profile.user_id, picture_data)

            assert result == new_profile
            mock_create.assert_called_once()
            mock_update.assert_called_once()


class TestProfileServiceDelete:
    """Test ProfileService delete method."""

    def test_delete_profile_success(self, profile_service: ProfileService, mock_profile: Profile):
        """Test deleting profile successfully."""
        with (
            patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get,
            patch("app.services.profile.ProfileRepository.delete") as mock_delete,
        ):
            mock_get.return_value = mock_profile
            db = MagicMock(spec=Session)

            profile_service.delete(db, mock_profile.user_id)

            mock_get.assert_called_once_with(db, mock_profile.user_id)
            mock_delete.assert_called_once_with(db, mock_profile)

    def test_delete_profile_not_found_raises_404(self, profile_service: ProfileService):
        """Test deleting non-existent profile raises 404."""
        with patch("app.services.profile.ProfileRepository.get_by_user_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                profile_service.delete(db, uuid.uuid4())

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
