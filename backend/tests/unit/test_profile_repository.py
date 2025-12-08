"""
Unit tests for ProfileRepository.

Tests the data access layer for profile operations.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.user import User
from app.repository.profile import ProfileRepository


class TestProfileRepositoryGet:
    """Test ProfileRepository get methods."""

    def test_get_by_user_id_found(self, db_session: Session, test_profile: Profile):
        """Test getting profile by user_id when exists."""
        result = ProfileRepository.get_by_user_id(db_session, test_profile.user_id)

        assert result is not None
        assert result.id == test_profile.id
        assert result.user_id == test_profile.user_id

    def test_get_by_user_id_not_found(self, db_session: Session):
        """Test getting profile by user_id when doesn't exist."""
        fake_user_id = uuid.uuid4()
        result = ProfileRepository.get_by_user_id(db_session, fake_user_id)

        assert result is None

    def test_get_by_id_found(self, db_session: Session, test_profile: Profile):
        """Test getting profile by ID when exists."""
        result = ProfileRepository.get_by_id(db_session, test_profile.id)

        assert result is not None
        assert result.id == test_profile.id

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting profile by ID when doesn't exist."""
        fake_id = uuid.uuid4()
        result = ProfileRepository.get_by_id(db_session, fake_id)

        assert result is None


class TestProfileRepositoryCreate:
    """Test ProfileRepository create method."""

    def test_create_profile_success(self, db_session: Session, test_user: User):
        """Test creating a new profile."""
        # Prepare data as service would (convert schema to dict)
        profile_data = {
            "name": "Test User",
            "campus": "Main Campus",
            "contact_info": {"email": "test@example.edu"},
        }

        result = ProfileRepository.create(db_session, test_user.id, profile_data)

        assert result.id is not None
        assert result.user_id == test_user.id
        assert result.name == "Test User"
        assert result.campus == "Main Campus"
        assert result.contact_info == {"email": "test@example.edu"}
        assert result.created_at is not None

    def test_create_profile_minimal(self, db_session: Session, test_user: User):
        """Test creating profile with only required fields."""
        profile_data = {
            "name": "Minimal User",
            "campus": None,
            "contact_info": None,
        }

        result = ProfileRepository.create(db_session, test_user.id, profile_data)

        assert result.name == "Minimal User"
        assert result.campus is None
        assert result.contact_info is None

    def test_create_profile_then_add_picture(self, db_session: Session, test_user: User):
        """Test creating profile then adding picture separately."""
        profile_data = {
            "name": "User",
            "campus": None,
            "contact_info": None,
        }

        result = ProfileRepository.create(db_session, test_user.id, profile_data)
        assert result.profile_picture_url is None

        # Add picture using update_profile_picture
        updated = ProfileRepository.update_profile_picture(
            db_session, result, "https://example.com/pic.jpg"
        )
        assert updated.profile_picture_url == "https://example.com/pic.jpg"


class TestProfileRepositoryUpdate:
    """Test ProfileRepository update method."""

    def test_update_profile_name(self, db_session: Session, test_profile: Profile):
        """Test updating profile name."""
        update_data = {"name": "Updated Name"}

        result = ProfileRepository.update(db_session, test_profile, update_data)

        assert result.name == "Updated Name"
        assert result.id == test_profile.id

    def test_update_profile_multiple_fields(self, db_session: Session, test_profile: Profile):
        """Test updating multiple profile fields."""
        update_data = {
            "name": "New Name",
            "campus": "New Campus",
            "contact_info": {"phone": "123-456-7890"},
        }

        result = ProfileRepository.update(db_session, test_profile, update_data)

        assert result.name == "New Name"
        assert result.campus == "New Campus"
        assert result.contact_info == {"phone": "123-456-7890"}

    def test_update_profile_picture(self, db_session: Session, test_profile: Profile):
        """Test updating profile picture using update_profile_picture method."""
        result = ProfileRepository.update_profile_picture(
            db_session, test_profile, "https://example.com/new.jpg"
        )

        assert result.profile_picture_url == "https://example.com/new.jpg"

    def test_update_profile_clear_optional(self, db_session: Session, test_profile: Profile):
        """Test clearing optional fields."""
        update_data = {"campus": None, "contact_info": None}

        result = ProfileRepository.update(db_session, test_profile, update_data)

        assert result.campus is None
        assert result.contact_info is None

    def test_update_profile_no_changes(self, db_session: Session, test_profile: Profile):
        """Test update with no changes returns same profile."""
        update_data = {}

        result = ProfileRepository.update(db_session, test_profile, update_data)

        assert result.id == test_profile.id
        assert result.name == test_profile.name


class TestProfileRepositoryDelete:
    """Test ProfileRepository delete method."""

    def test_delete_profile(self, db_session: Session, test_profile: Profile):
        """Test deleting a profile."""
        profile_id = test_profile.id

        ProfileRepository.delete(db_session, test_profile)

        # Verify profile is deleted
        result = ProfileRepository.get_by_id(db_session, profile_id)
        assert result is None

    def test_delete_removes_from_session(self, db_session: Session, test_profile: Profile):
        """Test that delete removes profile from session."""
        ProfileRepository.delete(db_session, test_profile)

        assert test_profile not in db_session
