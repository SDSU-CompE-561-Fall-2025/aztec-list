"""
User service.

This module contains business logic for user operations.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash, verify_password
from app.core.security import ensure_not_banned
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.repository.user import UserRepository
from app.schemas.user import UserCreate


class UserService:
    """Service for user business logic."""

    def get_by_email(self, db: Session, email: str) -> User:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User: User object

        Raises:
            HTTPException: If user not found
        """
        user = UserRepository.get_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{email}' not found",
            )
        return user

    def get_by_username(self, db: Session, username: str) -> User:
        """
        Get user by username.

        Args:
            db: Database session
            username: User username

        Returns:
            User: User object

        Raises:
            HTTPException: If user not found
        """
        user = UserRepository.get_by_username(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username '{username}' not found",
            )
        return user

    def get_by_id(self, db: Session, user_id: uuid.UUID) -> User:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID (UUID)

        Returns:
            User: User object

        Raises:
            HTTPException: If user not found
        """
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return user

    def create(self, db: Session, user: UserCreate) -> User:
        """
        Create a new user with validation.

        Args:
            db: Database session
            user: User creation data

        Returns:
            User: Created user

        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        existing_user = UserRepository.get_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        existing_user = UserRepository.get_by_username(db, user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        hashed_password = get_password_hash(user.password)
        return UserRepository.create(db, user, hashed_password)

    def delete(self, db: Session, user_id: uuid.UUID) -> None:
        """
        Delete a user by ID.

        Args:
            db: Database session
            user_id: User ID (UUID) to delete

        Raises:
            HTTPException: If user not found
        """
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        UserRepository.delete(db, user)

    def authenticate(self, db: Session, username: str, password: str) -> User:
        """
        Authenticate user with username or email and password.

        Args:
            db: Database session
            username: User email or username
            password: Plain text password

        Returns:
            User: Authenticated user if credentials are valid

        Raises:
            HTTPException: 401 if credentials are invalid, 403 if user is banned
        """
        user = UserRepository.get_by_email_or_username(db, username)

        # Validate credentials
        if not user or not verify_password(password, str(user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        actions = AdminActionRepository.get_by_target_user_id(db, user.id)
        ensure_not_banned(actions)

        return user


# Create a singleton instance
user_service = UserService()
