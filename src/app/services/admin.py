"""
Admin action service.

This module contains business logic for admin action operations.
"""

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.admin import AdminAction
from app.repository.admin import AdminActionRepository
from app.repository.user import UserRepository
from app.schemas.admin import (
    ActionType,
    AdminActionBan,
    AdminActionCreate,
    AdminActionStrike,
    AdminActionWarning,
)


class AdminActionService:
    """Service for admin action business logic."""

    def get_by_id(self, db: Session, action_id: uuid.UUID) -> AdminAction:
        """
        Get admin action by ID.

        Args:
            db: Database session
            action_id: Admin action ID (UUID)

        Returns:
            AdminAction: Admin action object

        Raises:
            HTTPException: If admin action not found
        """
        action = AdminActionRepository.get_by_id(db, action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin action with ID {action_id} not found",
            )
        return action

    def get_by_target_user_id(self, db: Session, target_user_id: uuid.UUID) -> list[AdminAction]:
        """
        Get all admin actions for a specific target user.

        Args:
            db: Database session
            target_user_id: Target user ID (UUID)

        Returns:
            list[AdminAction]: List of admin actions targeting the user
        """
        return AdminActionRepository.get_by_target_user_id(db, target_user_id)

    def get_by_target_listing_id(
        self, db: Session, target_listing_id: uuid.UUID
    ) -> list[AdminAction]:
        """
        Get all admin actions for a specific target listing.

        Args:
            db: Database session
            target_listing_id: Target listing ID (UUID)

        Returns:
            list[AdminAction]: List of admin actions targeting the listing
        """
        return AdminActionRepository.get_by_target_listing_id(db, target_listing_id)

    def get_filtered(  # noqa: PLR0913
        self,
        db: Session,
        target_user_id: uuid.UUID | None = None,
        admin_id: uuid.UUID | None = None,
        action_type: ActionType | None = None,
        target_listing_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AdminAction], int]:
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
            tuple[list[AdminAction], int]: Filtered admin actions and total count
        """
        actions = AdminActionRepository.get_filtered(
            db=db,
            target_user_id=target_user_id,
            admin_id=admin_id,
            action_type=action_type,
            target_listing_id=target_listing_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

        count = AdminActionRepository.count_filtered(
            db=db,
            target_user_id=target_user_id,
            admin_id=admin_id,
            action_type=action_type,
            target_listing_id=target_listing_id,
            from_date=from_date,
            to_date=to_date,
        )

        return actions, count

    def create(self, db: Session, admin_id: uuid.UUID, action: AdminActionCreate) -> AdminAction:
        """
        Create a new admin action with validation.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            action: Admin action creation data

        Returns:
            AdminAction: Created admin action

        Raises:
            HTTPException: If target user not found or listing_removal missing target_listing_id
        """
        # Validate target user exists
        target_user = UserRepository.get_by_id(db, action.target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target user with ID {action.target_user_id} not found",
            )

        # Validate listing_removal requires target_listing_id
        if action.action_type == ActionType.LISTING_REMOVAL and not action.target_listing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_listing_id is required when action_type is listing_removal",
            )

        return AdminActionRepository.create(db, admin_id, action)

    def create_warning(
        self,
        db: Session,
        admin_id: uuid.UUID,
        target_user_id: uuid.UUID,
        warning: AdminActionWarning,
    ) -> AdminAction:
        """
        Create a warning action (convenience method).

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID to warn
            warning: Warning data with reason

        Returns:
            AdminAction: Created warning action

        Raises:
            HTTPException: If target user not found
        """
        # Validate target user exists
        target_user = UserRepository.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {target_user_id} not found",
            )

        # Create AdminActionCreate from warning
        action = AdminActionCreate(
            target_user_id=target_user_id,
            action_type=ActionType.WARNING,
            reason=warning.reason,
            target_listing_id=None,
            expires_at=None,
        )

        return AdminActionRepository.create(db, admin_id, action)

    def create_strike(
        self, db: Session, admin_id: uuid.UUID, target_user_id: uuid.UUID, strike: AdminActionStrike
    ) -> AdminAction:
        """
        Create a strike action (convenience method).

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID to strike
            strike: Strike data with reason

        Returns:
            AdminAction: Created strike action

        Raises:
            HTTPException: If target user not found
        """
        # Validate target user exists
        target_user = UserRepository.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {target_user_id} not found",
            )

        # Create AdminActionCreate from strike
        action = AdminActionCreate(
            target_user_id=target_user_id,
            action_type=ActionType.STRIKE,
            reason=strike.reason,
            target_listing_id=None,
            expires_at=None,
        )

        return AdminActionRepository.create(db, admin_id, action)

    def create_ban(
        self, db: Session, admin_id: uuid.UUID, target_user_id: uuid.UUID, ban: AdminActionBan
    ) -> AdminAction:
        """
        Create a ban action (convenience method).

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID to ban
            ban: Ban data with reason and optional expires_at

        Returns:
            AdminAction: Created ban action

        Raises:
            HTTPException: If target user not found
        """
        # Validate target user exists
        target_user = UserRepository.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {target_user_id} not found",
            )

        # Create AdminActionCreate from ban
        action = AdminActionCreate(
            target_user_id=target_user_id,
            action_type=ActionType.BAN,
            reason=ban.reason,
            target_listing_id=None,
            expires_at=ban.expires_at,
        )

        return AdminActionRepository.create(db, admin_id, action)

    def delete(self, db: Session, action_id: uuid.UUID) -> None:
        """
        Delete (revoke) an admin action by ID.

        Args:
            db: Database session
            action_id: Admin action ID (UUID) to delete

        Raises:
            HTTPException: If admin action not found
        """
        action = AdminActionRepository.get_by_id(db, action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin action with ID {action_id} not found",
            )

        AdminActionRepository.delete(db, action)


# Create a singleton instance
admin_action_service = AdminActionService()
