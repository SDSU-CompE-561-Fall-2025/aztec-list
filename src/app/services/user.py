"""
User service.

This module contains business logic for user operations.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash, verify_password
from app.models.user import User
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

    def get_by_id(self, db: Session, user_id: int) -> User:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

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

    def authenticate(self, db: Session, username: str, password: str) -> User | None:
        """
        Authenticate user with username or email and password.

        Args:
            db: Database session
            username: User email or username
            password: Plain text password

        Returns:
            User | None: Authenticated user if credentials are valid, None otherwise
        """
        # Try to find user by email first
        user = UserRepository.get_by_email(db, username)

        # If not found by email, try username
        if not user:
            user = UserRepository.get_by_username(db, username)

        # If user not found or password incorrect, return None
        if not user:
            return None
        if not verify_password(password, str(user.hashed_password)):
            return None
        return user


# Create a singleton instance
user_service = UserService()
