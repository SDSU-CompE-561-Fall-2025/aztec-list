"""
Unit tests for UserRepository.

Tests the data access layer for user operations.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.repository.user import UserRepository
from app.schemas.user import UserCreate


class TestUserRepositoryGet:
    """Test UserRepository get methods."""

    def test_get_by_email_found(self, db_session: Session, test_user: User):
        """Test getting user by email when exists."""
        result = UserRepository.get_by_email(db_session, test_user.email)

        assert result is not None
        assert result.id == test_user.id
        assert result.email == test_user.email

    def test_get_by_email_not_found(self, db_session: Session):
        """Test getting user by email when doesn't exist."""
        result = UserRepository.get_by_email(db_session, "nonexistent@example.com")

        assert result is None

    def test_get_by_username_found(self, db_session: Session, test_user: User):
        """Test getting user by username when exists."""
        result = UserRepository.get_by_username(db_session, test_user.username)

        assert result is not None
        assert result.id == test_user.id
        assert result.username == test_user.username

    def test_get_by_username_not_found(self, db_session: Session):
        """Test getting user by username when doesn't exist."""
        result = UserRepository.get_by_username(db_session, "nonexistent_user")

        assert result is None

    def test_get_by_email_or_username_with_email(self, db_session: Session, test_user: User):
        """Test getting user by email using email_or_username method."""
        result = UserRepository.get_by_email_or_username(db_session, test_user.email)

        assert result is not None
        assert result.id == test_user.id

    def test_get_by_email_or_username_with_username(self, db_session: Session, test_user: User):
        """Test getting user by username using email_or_username method."""
        result = UserRepository.get_by_email_or_username(db_session, test_user.username)

        assert result is not None
        assert result.id == test_user.id

    def test_get_by_email_or_username_not_found(self, db_session: Session):
        """Test email_or_username returns None when user doesn't exist."""
        result = UserRepository.get_by_email_or_username(db_session, "nonexistent")

        assert result is None

    def test_get_by_id_found(self, db_session: Session, test_user: User):
        """Test getting user by ID when exists."""
        result = UserRepository.get_by_id(db_session, test_user.id)

        assert result is not None
        assert result.id == test_user.id

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting user by ID when doesn't exist."""
        fake_id = uuid.uuid4()
        result = UserRepository.get_by_id(db_session, fake_id)

        assert result is None


class TestUserRepositoryCreate:
    """Test UserRepository create method."""

    def test_create_user_success(self, db_session: Session):
        """Test creating a new user."""
        user_data = UserCreate(
            username="newuser", email="newuser@example.com", password="password123"
        )
        hashed_password = "hashed_password_123"

        result = UserRepository.create(db_session, user_data, hashed_password)

        assert result.id is not None
        assert result.username == "newuser"
        assert result.email == "newuser@example.com"
        assert result.hashed_password == hashed_password
        assert result.created_at is not None

        # Verify it's in the database
        db_user = UserRepository.get_by_id(db_session, result.id)
        assert db_user is not None
        assert db_user.username == "newuser"

    def test_create_user_with_defaults(self, db_session: Session):
        """Test that new users get default values."""
        user_data = UserCreate(
            username="defaultuser", email="default@example.com", password="password123"
        )

        result = UserRepository.create(db_session, user_data, "hashed")

        assert result.is_verified is False  # Default value
        assert result.role.value == "user"  # Default role


class TestUserRepositoryUpdate:
    """Test UserRepository update method."""

    def test_update_user(self, db_session: Session, test_user: User):
        """Test updating user attributes."""
        original_username = test_user.username
        test_user.username = "updated_username"
        test_user.email = "updated@example.com"

        result = UserRepository.update(db_session, test_user)

        assert result.username == "updated_username"
        assert result.email == "updated@example.com"

        # Verify changes persisted
        db_user = UserRepository.get_by_id(db_session, test_user.id)
        assert db_user.username == "updated_username"
        assert db_user.username != original_username

    def test_update_refreshes_instance(self, db_session: Session, test_user: User):
        """Test that update refreshes the instance with database state."""
        # Modify the user object
        test_user.username = "updated_username"

        # Update via repository (should commit and refresh)
        result = UserRepository.update(db_session, test_user)

        # Instance should be updated
        assert result.username == "updated_username"
        assert result is test_user  # Same instance, refreshed


class TestUserRepositoryDelete:
    """Test UserRepository delete method."""

    def test_delete_user(self, db_session: Session, test_user: User):
        """Test deleting a user."""
        user_id = test_user.id

        UserRepository.delete(db_session, test_user)

        # Verify user is deleted
        result = UserRepository.get_by_id(db_session, user_id)
        assert result is None

    def test_delete_removes_from_session(self, db_session: Session, test_user: User):
        """Test that delete removes user from session."""
        UserRepository.delete(db_session, test_user)

        # Attempting to access deleted object should raise or return None
        assert test_user not in db_session
