"""
Admin action repository.

This module provides data access layer for admin action operations.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import AdminAction
from app.schemas.admin import ActionType, AdminActionCreate


class AdminActionRepository:
    """Repository for admin action data access."""

    @staticmethod
    def get_by_id(db: Session, action_id: uuid.UUID) -> AdminAction | None:
        """
        Get admin action by ID.

        Args:
            db: Database session
            action_id: Admin action ID (UUID)

        Returns:
            AdminAction | None: Admin action if found, None otherwise
        """
        return db.get(AdminAction, action_id)

    @staticmethod
    def get_by_target_user_id(db: Session, target_user_id: uuid.UUID) -> list[AdminAction]:
        """
        Get all admin actions for a specific target user.

        Args:
            db: Database session
            target_user_id: Target user ID (UUID)

        Returns:
            list[AdminAction]: List of admin actions targeting the user
        """
        query = (
            select(AdminAction)
            .where(AdminAction.target_user_id == target_user_id)
            .order_by(AdminAction.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_by_admin_id(db: Session, admin_id: uuid.UUID) -> list[AdminAction]:
        """
        Get all admin actions performed by a specific admin.

        Args:
            db: Database session
            admin_id: Admin user ID (UUID)

        Returns:
            list[AdminAction]: List of admin actions performed by the admin
        """
        query = (
            select(AdminAction)
            .where(AdminAction.admin_id == admin_id)
            .order_by(AdminAction.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_by_listing_id(db: Session, listing_id: uuid.UUID) -> list[AdminAction]:
        """
        Get all admin actions for a specific listing.

        Args:
            db: Database session
            listing_id: Listing ID (UUID)

        Returns:
            list[AdminAction]: List of admin actions for the listing
        """
        query = (
            select(AdminAction)
            .where(AdminAction.target_listing_id == listing_id)
            .order_by(AdminAction.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_by_action_type(db: Session, action_type: ActionType) -> list[AdminAction]:
        """
        Get all admin actions of a specific type.

        Args:
            db: Database session
            action_type: Type of admin action

        Returns:
            list[AdminAction]: List of admin actions of the specified type
        """
        query = (
            select(AdminAction)
            .where(AdminAction.action_type == action_type.value)
            .order_by(AdminAction.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_all(
        db: Session,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AdminAction]:
        """
        Get all admin actions with pagination.

        Args:
            db: Database session
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            list[AdminAction]: List of admin actions
        """
        query = (
            select(AdminAction).order_by(AdminAction.created_at.desc()).limit(limit).offset(offset)
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_filtered(  # noqa: PLR0913
        db: Session,
        target_user_id: uuid.UUID | None = None,
        admin_id: uuid.UUID | None = None,
        action_type: ActionType | None = None,
        target_listing_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AdminAction]:
        """
        Get admin actions with optional filters and pagination.

        Args:
            db: Database session
            target_user_id: Filter by target user ID
            admin_id: Filter by admin user ID
            action_type: Filter by action type
            target_listing_id: Filter by listing ID
            from_date: Filter actions created on or after this date
            to_date: Filter actions created on or before this date
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            list[AdminAction]: List of filtered admin actions
        """
        query = select(AdminAction)

        if target_user_id:
            query = query.where(AdminAction.target_user_id == target_user_id)
        if admin_id:
            query = query.where(AdminAction.admin_id == admin_id)
        if action_type:
            query = query.where(AdminAction.action_type == action_type.value)
        if target_listing_id:
            query = query.where(AdminAction.target_listing_id == target_listing_id)
        if from_date:
            query = query.where(AdminAction.created_at >= from_date)
        if to_date:
            query = query.where(AdminAction.created_at <= to_date)

        query = query.order_by(AdminAction.created_at.desc()).limit(limit).offset(offset)
        return list(db.scalars(query).all())

    @staticmethod
    def count_filtered(  # noqa: PLR0913
        db: Session,
        target_user_id: uuid.UUID | None = None,
        admin_id: uuid.UUID | None = None,
        action_type: ActionType | None = None,
        target_listing_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """
        Count admin actions with optional filters.

        Args:
            db: Database session
            target_user_id: Filter by target user ID
            admin_id: Filter by admin user ID
            action_type: Filter by action type
            target_listing_id: Filter by listing ID
            from_date: Filter actions created on or after this date
            to_date: Filter actions created on or before this date

        Returns:
            int: Count of matching admin actions
        """
        query = select(AdminAction)

        if target_user_id:
            query = query.where(AdminAction.target_user_id == target_user_id)
        if admin_id:
            query = query.where(AdminAction.admin_id == admin_id)
        if action_type:
            query = query.where(AdminAction.action_type == action_type.value)
        if target_listing_id:
            query = query.where(AdminAction.target_listing_id == target_listing_id)
        if from_date:
            query = query.where(AdminAction.created_at >= from_date)
        if to_date:
            query = query.where(AdminAction.created_at <= to_date)

        return db.scalar(select(AdminAction).count()) or 0

    @staticmethod
    def create(db: Session, admin_id: uuid.UUID, action: AdminActionCreate) -> AdminAction:
        """
        Create a new admin action.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            action: Admin action creation data

        Returns:
            AdminAction: Created admin action
        """
        db_action = AdminAction(
            admin_id=admin_id,
            target_user_id=action.target_user_id,
            action_type=action.action_type.value,
            reason=action.reason,
            target_listing_id=action.target_listing_id,
            expires_at=action.expires_at,
        )
        db.add(db_action)
        db.commit()
        db.refresh(db_action)
        return db_action

    @staticmethod
    def delete(db: Session, db_action: AdminAction) -> None:
        """
        Delete admin action (revoke).

        Args:
            db: Database session
            db_action: Admin action instance to delete
        """
        db.delete(db_action)
        db.commit()
