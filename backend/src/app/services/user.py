"""
User service.

This module contains business logic for user operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.auth import get_password_hash, verify_password
from app.core.email import email_service
from app.core.security import generate_verification_token, get_verification_token_expiry
from app.repository.admin import AdminActionRepository
from app.repository.user import UserRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.user import User
    from app.schemas.user import UserCreate, UserUpdate


logger = logging.getLogger(__name__)


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

    def search(self, db: Session, query: str, limit: int = 10) -> list[User]:
        """
        Search users by username or email.

        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results (default 10)

        Returns:
            list[User]: List of matching users
        """
        if not query or not query.strip():
            return []
        return UserRepository.search(db, query.strip(), limit)

    def create(self, db: Session, user: UserCreate) -> tuple[User, bool]:
        """
        Create a new user with validation and send verification email.

        Args:
            db: Database session
            user: User creation data

        Returns:
            tuple[User, bool]: Created user and email sending status

        Raises:
            HTTPException: If email already exists
        """
        if UserRepository.get_by_email(db, user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if UserRepository.get_by_username(db, user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Create user
        hashed_password = get_password_hash(user.password)
        db_user = UserRepository.create(db, user, hashed_password)

        # Generate and set verification token
        verification_token = generate_verification_token()
        expiry = get_verification_token_expiry()
        UserRepository.set_verification_token(db, db_user, verification_token, expiry)

        # Send verification email (non-blocking - failure doesn't prevent signup)
        email_sent = email_service.send_email_verification(
            email=db_user.email,
            username=db_user.username,
            verification_token=verification_token,
        )

        if not email_sent:
            logger.warning(
                "Failed to send verification email during user creation",
                extra={"user_id": str(db_user.id), "email": db_user.email},
            )

        return db_user, email_sent

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
        if not user or not verify_password(password, str(user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user has an active ban
        ban = AdminActionRepository.has_active_ban(db, user.id)
        if ban:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account banned. Contact support for assistance.",
            )

        return user

    def update(self, db: Session, user_id: uuid.UUID, update_data: UserUpdate) -> tuple[User, bool]:
        """
        Update user information.

        Args:
            db: Database session
            user_id: ID of user to update
            update_data: New user data

        Returns:
            tuple[User, bool]: Updated user and email sending status (True if email not changed)

        Raises:
            HTTPException: 404 if user not found, 400 if username/email taken
        """
        user = self.get_by_id(db, user_id)
        email_sent = True  # Default to True if no email change

        if update_data.username and update_data.username != user.username:
            if UserRepository.get_by_username(db, update_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )
            user.username = update_data.username

        if update_data.email and update_data.email != user.email:
            if UserRepository.get_by_email(db, str(update_data.email)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            user.email = update_data.email
            user.is_verified = False

            # Generate new verification token for new email
            verification_token = generate_verification_token()
            expiry = get_verification_token_expiry()
            UserRepository.set_verification_token(db, user, verification_token, expiry)

            # Send verification email to new address
            email_sent = email_service.send_email_verification(
                email=user.email,
                username=user.username,
                verification_token=verification_token,
            )

            if not email_sent:
                logger.warning(
                    "Failed to send verification email during email change",
                    extra={
                        "user_id": str(user.id),
                        "old_email": user.email,
                        "new_email": update_data.email,
                    },
                )

        return UserRepository.update(db, user), email_sent

    def change_password(
        self, db: Session, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        """
        Change user's password.

        Args:
            db: Database session
            user_id: ID of user changing password
            current_password: Current password for verification
            new_password: New password to set

        Raises:
            HTTPException: 404 if user not found, 401 if current password is incorrect
        """
        user = self.get_by_id(db, user_id)

        # Verify current password
        if not verify_password(current_password, str(user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        # Hash and update new password
        user.hashed_password = get_password_hash(new_password)
        UserRepository.update(db, user)

    def verify_user(self, db: Session, user_id: uuid.UUID) -> User:
        """
        Manually verify a user's email (admin action).

        Clears verification token/expiry when verified.

        Args:
            db: Database session
            user_id: ID of user to verify

        Returns:
            User: Updated user

        Raises:
            HTTPException: 404 if user not found
        """
        user = self.get_by_id(db, user_id)

        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None

        return UserRepository.update(db, user)

    def unverify_user(self, db: Session, user_id: uuid.UUID) -> User:
        """
        Manually unverify a user's email (admin action).

        Used if verification was obtained fraudulently.

        Args:
            db: Database session
            user_id: ID of user to unverify

        Returns:
            User: Updated user

        Raises:
            HTTPException: 404 if user not found
        """
        user = self.get_by_id(db, user_id)
        user.is_verified = False

        return UserRepository.update(db, user)


# Create a singleton instance
user_service = UserService()
