"""User service.

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

    def __init__(self) -> None:
        """Initialize user service."""
        self.repository = UserRepository()

    def get_by_email(self, db: Session, email: str) -> User | None:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User | None: User if found, None otherwise
        """
        return self.repository.get_by_email(db, email)

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User | None: User if found, None otherwise
        """
        return self.repository.get_by_id(db, user_id)

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
        existing_user = self.repository.get_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password and create user
        hashed_password = get_password_hash(user.password)
        return self.repository.create(db, user, hashed_password)

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User | None: Authenticated user if credentials are valid, None otherwise
        """
        user = self.repository.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, str(user.hashed_password)):
            return None
        return user


# Create a singleton instance
user_service = UserService()
