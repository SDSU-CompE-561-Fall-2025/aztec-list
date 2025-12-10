"""
User repository.

This module provides data access layer for user operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import or_, select

from app.models.user import User

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.schemas.user import UserCreate


class UserRepository:
    """Repository for user data access."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User | None: User if found, None otherwise
        """
        query = select(User).where(User.email == email)
        return db.scalars(query).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        """
        Get user by username.

        Args:
            db: Database session
            username: User username

        Returns:
            User | None: User if found, None otherwise
        """
        query = select(User).where(User.username == username)
        return db.scalars(query).first()

    @staticmethod
    def get_by_email_or_username(db: Session, identifier: str) -> User | None:
        """
        Get user by email or username in a single query.

        Args:
            db: Database session
            identifier: User email or username

        Returns:
            User | None: User if found, None otherwise
        """
        query = select(User).where(or_(User.email == identifier, User.username == identifier))
        return db.scalars(query).first()

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID (UUID)

        Returns:
            User | None: User if found, None otherwise
        """
        return db.get(User, user_id)

    @staticmethod
    def create(db: Session, user: UserCreate, hashed_password: str) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user: User creation data
            hashed_password: Hashed password

        Returns:
            User: Created user
        """
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update(db: Session, db_user: User) -> User:
        """
        Update user.

        Args:
            db: Database session
            db_user: User instance to update

        Returns:
            User: Updated user
        """
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete(db: Session, db_user: User) -> None:
        """
        Delete user.

        Args:
            db: Database session
            db_user: User instance to delete
        """
        db.delete(db_user)
        db.commit()

    @staticmethod
    def get_by_verification_token(db: Session, token: str) -> User | None:
        """
        Get user by verification token.

        Args:
            db: Database session
            token: Verification token

        Returns:
            User | None: User if found with valid token, None otherwise
        """
        return (
            db.query(User)
            .filter(
                User.verification_token == token,
                User.verification_token_expires > datetime.now(UTC),
            )
            .first()
        )

    @staticmethod
    def set_verification_token(db: Session, db_user: User, token: str, expires: datetime) -> User:
        """
        Set verification token and expiry for user.

        Args:
            db: Database session
            db_user: User instance
            token: Verification token
            expires: Token expiration datetime

        Returns:
            User: Updated user
        """
        db_user.verification_token = token
        db_user.verification_token_expires = expires
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def mark_as_verified(db: Session, db_user: User) -> User:
        """
        Mark user as verified and clear verification token.

        Args:
            db: Database session
            db_user: User instance

        Returns:
            User: Updated user
        """
        db_user.is_verified = True
        db_user.verification_token = None
        db_user.verification_token_expires = None
        db.commit()
        db.refresh(db_user)
        return db_user
