"""
Admin action repository.

This module provides data access layer for admin action operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.core.enums import AdminActionType
from app.models.admin import AdminAction
from app.models.user import User

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.schemas.admin import AdminActionCreate, AdminActionFilters


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
    def has_active_ban(db: Session, user_id: uuid.UUID) -> AdminAction | None:
        """
        Check if user has an active ban.

        This is optimized to check only for BAN actions, avoiding fetching
        all admin actions for the user.

        Note: Revoked bans are hard-deleted, so any existing BAN is active.

        Args:
            db: Database session
            user_id: User ID to check

        Returns:
            AdminAction | None: The active ban action if found, None otherwise
        """
        query = (
            select(AdminAction)
            .where(
                AdminAction.target_user_id == user_id,
                AdminAction.action_type == AdminActionType.BAN,
            )
            .limit(1)
        )
        return db.scalars(query).first()

    @staticmethod
    def count_strikes(db: Session, user_id: uuid.UUID) -> int:
        """
        Count the number of active strikes for a user.

        This is optimized to count only STRIKE actions at the database level,
        avoiding fetching all admin actions for the user.

        Args:
            db: Database session
            user_id: User ID to check

        Returns:
            int: Number of strike actions for the user
        """
        query = select(func.count()).where(
            AdminAction.target_user_id == user_id,
            AdminAction.action_type == AdminActionType.STRIKE,
        )
        return db.scalar(query) or 0

    @staticmethod
    def get_by_target_listing_id(db: Session, target_listing_id: uuid.UUID) -> list[AdminAction]:
        """
        Get all admin actions for a specific target listing.

        Args:
            db: Database session
            target_listing_id: Target listing ID (UUID)

        Returns:
            list[AdminAction]: List of admin actions for the target listing
        """
        query = (
            select(AdminAction)
            .where(AdminAction.target_listing_id == target_listing_id)
            .order_by(AdminAction.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_by_action_type(db: Session, action_type: AdminActionType) -> list[AdminAction]:
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
    def get_filtered(
        db: Session, filters: AdminActionFilters
    ) -> list[tuple[AdminAction, str | None, str | None]]:
        """
        Get admin actions with optional filters and pagination.

        Returns actions with associated usernames as separate tuple elements
        rather than dynamically attaching attributes to model instances.

        Args:
            db: Database session
            filters: Filter parameters including target_user_id, admin_id, action_type,
                    target_listing_id, date ranges, and pagination

        Returns:
            list[tuple[AdminAction, str | None, str | None]]: List of tuples containing
                (action, admin_username, target_username)
        """
        # Create aliases for admin and target users
        admin_user = aliased(User, name="admin_user")
        target_user = aliased(User, name="target_user")

        query = (
            select(
                AdminAction,
                admin_user.username.label("admin_username"),
                target_user.username.label("target_username"),
            )
            .outerjoin(admin_user, AdminAction.admin_id == admin_user.id)
            .outerjoin(target_user, AdminAction.target_user_id == target_user.id)
        )

        if filters.target_user_id:
            query = query.where(AdminAction.target_user_id == filters.target_user_id)
        if filters.admin_id:
            query = query.where(AdminAction.admin_id == filters.admin_id)
        if filters.action_type:
            query = query.where(AdminAction.action_type == filters.action_type.value)
        if filters.target_listing_id:
            query = query.where(AdminAction.target_listing_id == filters.target_listing_id)
        if filters.from_date:
            query = query.where(AdminAction.created_at >= filters.from_date)
        if filters.to_date:
            query = query.where(AdminAction.created_at <= filters.to_date)

        query = (
            query.order_by(AdminAction.created_at.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )

        results = db.execute(query).all()

        # Return list of tuples (action, admin_username, target_username)
        return [(row[0], row[1], row[2]) for row in results]

    @staticmethod
    def count_filtered(db: Session, filters: AdminActionFilters) -> int:
        """
        Count admin actions with optional filters.

        Args:
            db: Database session
            filters: Filter parameters including target_user_id, admin_id, action_type,
                    target_listing_id, and date ranges

        Returns:
            int: Count of matching admin actions
        """
        query = select(AdminAction)

        if filters.target_user_id:
            query = query.where(AdminAction.target_user_id == filters.target_user_id)
        if filters.admin_id:
            query = query.where(AdminAction.admin_id == filters.admin_id)
        if filters.action_type:
            query = query.where(AdminAction.action_type == filters.action_type.value)
        if filters.target_listing_id:
            query = query.where(AdminAction.target_listing_id == filters.target_listing_id)
        if filters.from_date:
            query = query.where(AdminAction.created_at >= filters.from_date)
        if filters.to_date:
            query = query.where(AdminAction.created_at <= filters.to_date)

        count = db.scalar(select(func.count()).select_from(query.subquery()))
        return count if count is not None else 0

    @staticmethod
    def create(db: Session, admin_id: uuid.UUID, action: AdminActionCreate) -> AdminAction:
        """
        Create a new admin action and commit immediately.

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
    def create_no_commit(
        db: Session, admin_id: uuid.UUID, action: AdminActionCreate
    ) -> AdminAction:
        """
        Create a new admin action without committing (for transactional operations).

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            action: Admin action creation data

        Returns:
            AdminAction: Created admin action (not yet committed)
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
        db.flush()  # Assign ID but don't commit
        db.refresh(db_action)
        return db_action

    @staticmethod
    def delete(db: Session, db_action: AdminAction) -> None:
        """
        Delete admin action (revoke) and commit immediately.

        Args:
            db: Database session
            db_action: Admin action instance to delete
        """
        db.delete(db_action)
        db.commit()

    @staticmethod
    def delete_no_commit(db: Session, db_action: AdminAction) -> None:
        """
        Delete admin action without committing (for transactional operations).

        Args:
            db: Database session
            db_action: Admin action instance to delete
        """
        db.delete(db_action)
        db.flush()
