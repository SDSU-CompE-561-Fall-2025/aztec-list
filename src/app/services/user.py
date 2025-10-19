"""
User service.

This module contains business logic for user operations.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
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
            HTTPException: If user not found or database error occurs
        """
        try:
            user = UserRepository.get_by_email(db, email)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while fetching user",
            ) from e
        else:
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email '{email}' not found",
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
            HTTPException: If user not found or database error occurs
        """
        try:
            user = UserRepository.get_by_id(db, user_id)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while fetching user",
            ) from e
        else:
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
            HTTPException: If email already exists or database error occurs
        """
        # Check if user already exists
        existing_user = UserRepository.get_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        try:
            # Hash password and create user
            hashed_password = get_password_hash(user.password)
            return UserRepository.create(db, user, hashed_password)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while creating user",
            ) from e

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User | None: Authenticated user if credentials are valid, None otherwise

        Raises:
            HTTPException: If database error occurs
        """
        try:
            user = UserRepository.get_by_email(db, email)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred during authentication",
            ) from e
        else:
            if not user:
                return None
            if not verify_password(password, str(user.hashed_password)):
                return None
            return user


# Create a singleton instance
user_service = UserService()
