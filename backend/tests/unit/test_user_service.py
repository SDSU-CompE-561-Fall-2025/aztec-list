"""
Unit tests for UserService.

Tests the business logic layer for user operations.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AdminActionType, UserRole
from app.models.admin import AdminAction
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import UserService


@pytest.fixture
def user_service():
    """Create UserService instance."""
    return UserService()


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$hashedpassword",
        is_verified=True,
        role=UserRole.USER,
    )


class TestUserServiceGet:
    """Test UserService get methods."""

    def test_get_by_email_success(self, user_service: UserService, mock_user: User):
        """Test getting user by email when exists."""
        with patch("app.services.user.UserRepository.get_by_email") as mock_get:
            mock_get.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.get_by_email(db, "test@example.com")

            assert result == mock_user
            mock_get.assert_called_once_with(db, "test@example.com")

    def test_get_by_email_not_found_raises_404(self, user_service: UserService):
        """Test getting user by email when doesn't exist raises 404."""
        with patch("app.services.user.UserRepository.get_by_email") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.get_by_email(db, "nonexistent@example.com")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in exc_info.value.detail.lower()

    def test_get_by_username_success(self, user_service: UserService, mock_user: User):
        """Test getting user by username when exists."""
        with patch("app.services.user.UserRepository.get_by_username") as mock_get:
            mock_get.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.get_by_username(db, "testuser")

            assert result == mock_user
            mock_get.assert_called_once_with(db, "testuser")

    def test_get_by_username_not_found_raises_404(self, user_service: UserService):
        """Test getting user by username when doesn't exist raises 404."""
        with patch("app.services.user.UserRepository.get_by_username") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.get_by_username(db, "nonexistent")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in exc_info.value.detail.lower()

    def test_get_by_id_success(self, user_service: UserService, mock_user: User):
        """Test getting user by ID when exists."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.get_by_id(db, mock_user.id)

            assert result == mock_user
            mock_get.assert_called_once_with(db, mock_user.id)

    def test_get_by_id_not_found_raises_404(self, user_service: UserService):
        """Test getting user by ID when doesn't exist raises 404."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.get_by_id(db, random_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(random_id) in exc_info.value.detail

    def test_get_by_id_success(self, user_service: UserService, mock_user: User):
        """Test getting user by ID when exists."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.get_by_id(db, mock_user.id)

            assert result == mock_user
            mock_get.assert_called_once_with(db, mock_user.id)

    def test_get_by_id_not_found_raises_404(self, user_service: UserService):
        """Test getting user by ID when doesn't exist raises 404."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.get_by_id(db, random_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(random_id) in exc_info.value.detail


class TestUserServiceCreate:
    """Test UserService create method."""

    def test_create_user_success(self, user_service: UserService, mock_user: User):
        """Test creating a new user successfully."""
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123",
        )

        with (
            patch("app.services.user.UserRepository.get_by_email") as mock_get_email,
            patch("app.services.user.UserRepository.get_by_username") as mock_get_username,
            patch("app.services.user.UserRepository.create") as mock_create,
            patch("app.services.user.get_password_hash") as mock_hash,
        ):
            mock_get_email.return_value = None  # Email doesn't exist
            mock_get_username.return_value = None  # Username doesn't exist
            mock_hash.return_value = "hashed_password"
            mock_create.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.create(db, user_data)

            assert result == mock_user
            mock_get_email.assert_called_once_with(db, "new@example.com")
            mock_get_username.assert_called_once_with(db, "newuser")
            mock_hash.assert_called_once_with("password123")
            mock_create.assert_called_once_with(db, user_data, "hashed_password")

    def test_create_user_duplicate_email_raises_400(
        self, user_service: UserService, mock_user: User
    ):
        """Test creating user with duplicate email raises 400."""
        user_data = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="password123",
        )

        with patch("app.services.user.UserRepository.get_by_email") as mock_get:
            mock_get.return_value = mock_user  # Email already exists
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.create(db, user_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "email already registered" in exc_info.value.detail.lower()

    def test_create_user_duplicate_username_raises_400(
        self, user_service: UserService, mock_user: User
    ):
        """Test creating user with duplicate username raises 400."""
        user_data = UserCreate(
            username="existinguser",
            email="new@example.com",
            password="password123",
        )

        with (
            patch("app.services.user.UserRepository.get_by_email") as mock_get_email,
            patch("app.services.user.UserRepository.get_by_username") as mock_get_username,
        ):
            mock_get_email.return_value = None  # Email is unique
            mock_get_username.return_value = mock_user  # Username exists
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.create(db, user_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "username already registered" in exc_info.value.detail.lower()


class TestUserServiceAuthenticate:
    """Test UserService authenticate method."""

    def test_authenticate_success(self, user_service: UserService, mock_user: User):
        """Test successful authentication."""
        with (
            patch("app.services.user.UserRepository.get_by_email_or_username") as mock_get,
            patch("app.services.user.verify_password") as mock_verify,
            patch("app.services.user.AdminActionRepository.has_active_ban") as mock_ban_check,
        ):
            mock_get.return_value = mock_user
            mock_verify.return_value = True
            mock_ban_check.return_value = None  # No active ban
            db = MagicMock(spec=Session)

            result = user_service.authenticate(db, "testuser", "password123")

            assert result == mock_user
            mock_get.assert_called_once_with(db, "testuser")
            mock_verify.assert_called_once_with("password123", mock_user.hashed_password)
            mock_ban_check.assert_called_once_with(db, mock_user.id)

    def test_authenticate_invalid_username_raises_401(self, user_service: UserService):
        """Test authentication with invalid username raises 401."""
        with patch("app.services.user.UserRepository.get_by_email_or_username") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.authenticate(db, "nonexistent", "password123")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "incorrect" in exc_info.value.detail.lower()

    def test_authenticate_invalid_password_raises_401(
        self, user_service: UserService, mock_user: User
    ):
        """Test authentication with invalid password raises 401."""
        with (
            patch("app.services.user.UserRepository.get_by_email_or_username") as mock_get,
            patch("app.services.user.verify_password") as mock_verify,
        ):
            mock_get.return_value = mock_user
            mock_verify.return_value = False
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.authenticate(db, "testuser", "wrongpassword")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "incorrect" in exc_info.value.detail.lower()

    def test_authenticate_banned_user_raises_403(self, user_service: UserService, mock_user: User):
        """Test authentication for banned user raises 403."""
        ban_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=uuid.uuid4(),
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Banned",
        )

        with (
            patch("app.services.user.UserRepository.get_by_email_or_username") as mock_get,
            patch("app.services.user.verify_password") as mock_verify,
            patch("app.services.user.AdminActionRepository.has_active_ban") as mock_ban_check,
        ):
            mock_get.return_value = mock_user
            mock_verify.return_value = True
            mock_ban_check.return_value = ban_action  # Return active ban
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                user_service.authenticate(db, "testuser", "password123")

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "banned" in exc_info.value.detail.lower()
            mock_ban_check.assert_called_once_with(db, mock_user.id)


class TestUserServiceUpdate:
    """Test UserService update method."""

    def test_update_user_success(self, user_service: UserService, mock_user: User):
        """Test updating user successfully."""
        update_data = UserUpdate(username="updateduser")

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.get_by_username") as mock_check_username,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_check_username.return_value = None  # Username not taken
            # Just return the same user since we're mocking
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            result = user_service.update(db, mock_user.id, update_data)

            assert result == mock_user
            mock_get.assert_called_once_with(db, mock_user.id)
            mock_update.assert_called_once()

    def test_update_user_not_found_raises_404(self, user_service: UserService):
        """Test updating non-existent user raises 404."""
        update_data = UserUpdate(username="newname")

        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.update(db, random_id, update_data)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user_email_resets_verification(
        self, user_service: UserService, mock_user: User
    ):
        """Test updating email resets is_verified to False."""
        update_data = UserUpdate(email="newemail@example.com")
        mock_user.is_verified = True
        mock_user.email = "oldemail@example.com"

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.get_by_email") as mock_check_email,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_check_email.return_value = None  # New email not taken
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            user_service.update(db, mock_user.id, update_data)

            # Verify is_verified was set to False on the user object
            assert mock_user.is_verified is False
            mock_update.assert_called_once()

    def test_update_user_set_is_verified_true(
        self, user_service: UserService, mock_user: User
    ):
        """Test explicitly setting is_verified to True (admin operation)."""
        update_data = UserUpdate(is_verified=True)
        mock_user.is_verified = False

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            user_service.update(db, mock_user.id, update_data)

            # Verify is_verified was set to True
            assert mock_user.is_verified is True
            mock_update.assert_called_once()

    def test_update_user_set_is_verified_false(
        self, user_service: UserService, mock_user: User
    ):
        """Test explicitly setting is_verified to False."""
        update_data = UserUpdate(is_verified=False)
        mock_user.is_verified = True

        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            db = MagicMock(spec=Session)

            user_service.update(db, mock_user.id, update_data)

            # Verify is_verified was set to False
            assert mock_user.is_verified is False
            mock_update.assert_called_once()


class TestUserServiceDelete:
    """Test UserService delete method."""

    def test_delete_user_success(self, user_service: UserService, mock_user: User):
        """Test deleting user successfully."""
        with (
            patch("app.services.user.UserRepository.get_by_id") as mock_get,
            patch("app.services.user.UserRepository.delete") as mock_delete,
        ):
            mock_get.return_value = mock_user
            db = MagicMock(spec=Session)

            user_service.delete(db, mock_user.id)

            mock_get.assert_called_once_with(db, mock_user.id)
            mock_delete.assert_called_once_with(db, mock_user)

    def test_delete_user_not_found_raises_404(self, user_service: UserService):
        """Test deleting non-existent user raises 404."""
        with patch("app.services.user.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            random_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                user_service.delete(db, random_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(random_id) in exc_info.value.detail
