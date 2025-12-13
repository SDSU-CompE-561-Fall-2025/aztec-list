"""
Unit tests for UserService password management.

Tests for password change functionality.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.user import User
from app.services.user import UserService


@pytest.fixture
def user_service() -> UserService:
    """Create UserService instance for testing."""
    return UserService()


@pytest.fixture
def mock_user() -> User:
    """Create a mock user for testing."""
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.edu",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB3PwmZkOsC",  # "password"
        role=UserRole.USER,
        is_verified=True,
    )


class TestChangePassword:
    """Test UserService change_password method."""

    def test_change_password_success(self, user_service: UserService, mock_user: User):
        """Test changing password successfully."""
        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.verify_password") as mock_verify,
            patch("app.services.user.get_password_hash") as mock_hash,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"
            db = MagicMock(spec=Session)

            user_service.change_password(db, mock_user.id, "password", "new_password")

            mock_get.assert_called_once_with(db, mock_user.id)
            # Verify is called with current password before hashing the new one
            mock_verify.assert_called_once_with(
                "password", "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB3PwmZkOsC"
            )
            mock_hash.assert_called_once_with("new_password")
            assert mock_user.hashed_password == "new_hashed_password"
            mock_update.assert_called_once_with(db, mock_user)

    def test_change_password_incorrect_current_password_raises_401(
        self, user_service: UserService, mock_user: User
    ):
        """Test changing password with incorrect current password raises 401."""
        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.verify_password") as mock_verify,
        ):
            mock_get.return_value = mock_user
            mock_verify.return_value = False
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.change_password(db, mock_user.id, "wrong_password", "new_password")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "incorrect" in exc_info.value.detail.lower()

    def test_change_password_user_not_found_raises_404(self, user_service: UserService):
        """Test changing password for non-existent user raises 404."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.change_password(db, random_id, "old_pass", "new_pass")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestVerifyUser:
    """Test UserService verify_user method (admin action)."""

    def test_verify_user_success(self, user_service: UserService, mock_user: User):
        """Test manually verifying a user."""
        mock_user.is_verified = False
        mock_user.verification_token = "some_token"
        mock_user.verification_token_expires = "2024-12-31T23:59:59"

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.verify_user(db, mock_user.id)

            assert result.is_verified is True
            assert result.verification_token is None
            assert result.verification_token_expires is None
            mock_update.assert_called_once_with(db, mock_user)

    def test_verify_user_not_found_raises_404(self, user_service: UserService):
        """Test verifying non-existent user raises 404."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.verify_user(db, random_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_verify_already_verified_user(self, user_service: UserService, mock_user: User):
        """Test verifying already verified user still works."""
        mock_user.is_verified = True

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.verify_user(db, mock_user.id)

            assert result.is_verified is True
            mock_update.assert_called_once()


class TestUnverifyUser:
    """Test UserService unverify_user method (admin action)."""

    def test_unverify_user_success(self, user_service: UserService, mock_user: User):
        """Test manually unverifying a user."""
        mock_user.is_verified = True

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.unverify_user(db, mock_user.id)

            assert result.is_verified is False
            mock_update.assert_called_once_with(db, mock_user)

    def test_unverify_user_not_found_raises_404(self, user_service: UserService):
        """Test unverifying non-existent user raises 404."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.unverify_user(db, random_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_unverify_already_unverified_user(self, user_service: UserService, mock_user: User):
        """Test unverifying already unverified user still works."""
        mock_user.is_verified = False

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.unverify_user(db, mock_user.id)

            assert result.is_verified is False
            mock_update.assert_called_once()
