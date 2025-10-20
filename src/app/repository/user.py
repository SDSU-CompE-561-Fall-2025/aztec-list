"""
User repository.

This module provides data access layer for user operations.
"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User
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
        stmt = select(User).where(User.email == email)
        return db.scalars(stmt).first()

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
        stmt = select(User).where(User.username == username)
        return db.scalars(stmt).first()

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
        stmt = select(User).where(or_(User.email == identifier, User.username == identifier))
        return db.scalars(stmt).first()

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
