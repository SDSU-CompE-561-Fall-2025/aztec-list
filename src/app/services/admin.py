"""
Admin action service.

This module contains business logic for admin action operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.enums import AdminActionType, UserRole
from app.core.security import ensure_can_moderate_user
from app.core.settings import settings
from app.repository.admin import AdminActionRepository
from app.repository.listing import ListingRepository
from app.repository.user import UserRepository
from app.schemas.admin import AdminActionCreate, AdminActionStrike

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.admin import AdminAction
    from app.models.user import User
    from app.schemas.admin import AdminActionBan, AdminActionFilters


class AdminActionService:
    """Service for admin action business logic."""

    def _validate_moderation_participants(
        self, db: Session, admin_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> tuple[User, User]:
        """
        Validate and fetch both admin and target user for moderation actions.

        Centralizes validation logic and security checks for admin moderation.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID receiving the action

        Returns:
            tuple[User, User]: (target_user, admin_user)

        Raises:
            HTTPException: If either user not found or target is an admin
        """
        target_user = UserRepository.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {target_user_id} not found",
            )

        admin_user = UserRepository.get_by_id(db, admin_id)
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin with ID {admin_id} not found",
            )

        ensure_can_moderate_user(target_user, admin_user)
        return target_user, admin_user

    def _check_user_not_banned(self, db: Session, user_id: uuid.UUID) -> None:
        """
        Check if user is already banned.

        Args:
            db: Database session
            user_id: User ID to check

        Raises:
            HTTPException: If user is already banned
        """
        existing_actions = AdminActionRepository.get_by_target_user_id(db, user_id)
        for action in existing_actions:
            if action.action_type == AdminActionType.BAN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already banned. Revoke existing ban first if needed.",
                )

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

    def get_filtered(
        self,
        db: Session,
        filters: AdminActionFilters,
    ) -> tuple[list[AdminAction], int]:
        """
        Get admin actions with optional filters and pagination.

        Args:
            db: Database session
            filters: Filter criteria and pagination parameters

        Returns:
            tuple[list[AdminAction], int]: Filtered admin actions and total count
        """
        actions = AdminActionRepository.get_filtered(db=db, filters=filters)
        count = AdminActionRepository.count_filtered(db=db, filters=filters)
        return actions, count

    def _create_internal(
        self, db: Session, admin_id: uuid.UUID, action: AdminActionCreate
    ) -> AdminAction:
        """
        Create admin action without business logic checks (internal use only).

        Used by specialized methods (create_strike, create_ban) that handle
        their own validation. Should not be called directly from routes.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            action: Admin action creation data

        Returns:
            AdminAction: Created admin action

        Raises:
            HTTPException: If target user not found or listing_removal missing target_listing_id
        """
        target_user = UserRepository.get_by_id(db, action.target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target user with ID {action.target_user_id} not found",
            )

        if action.action_type == AdminActionType.LISTING_REMOVAL and not action.target_listing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_listing_id is required when action_type is listing_removal",
            )

        return AdminActionRepository.create(db, admin_id, action)

    def create_strike(
        self,
        db: Session,
        admin_id: uuid.UUID,
        target_user_id: uuid.UUID,
        strike: AdminActionStrike,
    ) -> AdminAction:
        """
        Create a strike action with auto-escalation to ban at threshold.

        Automatically issues a permanent ban if user reaches strike threshold.
        Prevents admins from striking other admins and already banned users.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID to strike
            strike: Strike data with reason

        Returns:
            AdminAction: Created strike action

        Raises:
            HTTPException: If target user not found, is admin, or already banned
        """
        self._validate_moderation_participants(db, admin_id, target_user_id)
        self._check_user_not_banned(db, target_user_id)

        action = AdminActionCreate(
            target_user_id=target_user_id,
            action_type=AdminActionType.STRIKE,
            reason=strike.reason,
            target_listing_id=None,
            expires_at=None,
        )
        created_strike = AdminActionRepository.create(db, admin_id, action)

        # Check for auto-escalation to permanent ban
        strike_count = self._count_active_strikes(db, target_user_id)
        if strike_count >= settings.moderation.strike_auto_ban_threshold:
            ban_action = AdminActionCreate(
                target_user_id=target_user_id,
                action_type=AdminActionType.BAN,
                reason=f"Automatic permanent ban: {strike_count} strikes accumulated. Latest: {strike.reason or 'Policy violation'}",
                target_listing_id=None,
                expires_at=None,
            )
            AdminActionRepository.create(db, admin_id, ban_action)

        return created_strike

    def _count_active_strikes(self, db: Session, user_id: uuid.UUID) -> int:
        """
        Count all strikes for a user.

        Args:
            db: Database session
            user_id: User ID to check

        Returns:
            int: Number of strikes
        """
        actions = AdminActionRepository.get_by_target_user_id(db, user_id)
        count = 0

        for action in actions:
            if action.action_type == AdminActionType.STRIKE:
                count += 1

        return count

    def create_ban(
        self, db: Session, admin_id: uuid.UUID, target_user_id: uuid.UUID, ban: AdminActionBan
    ) -> AdminAction:
        """
        Create a permanent ban action.

        Prevents admins from banning other admins and duplicate bans.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID to ban
            ban: Ban data with reason

        Returns:
            AdminAction: Created ban action

        Raises:
            HTTPException: If target user not found, is admin, or already banned
        """
        self._validate_moderation_participants(db, admin_id, target_user_id)
        self._check_user_not_banned(db, target_user_id)

        action = AdminActionCreate(
            target_user_id=target_user_id,
            action_type=AdminActionType.BAN,
            reason=ban.reason,
            target_listing_id=None,
            expires_at=None,
        )

        return AdminActionRepository.create(db, admin_id, action)

    def delete(self, db: Session, action_id: uuid.UUID, admin_id: uuid.UUID) -> None:
        """
        Delete (revoke) an admin action by ID.

        Prevents self-unbanning and maintains audit integrity.

        Args:
            db: Database session
            action_id: Admin action ID (UUID) to delete
            admin_id: Admin user ID performing the revocation

        Raises:
            HTTPException: If admin action not found or attempting to revoke own action
        """
        action = AdminActionRepository.get_by_id(db, action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin action with ID {action_id} not found",
            )

        if action.target_user_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot revoke actions targeting yourself. Contact another admin.",
            )

        AdminActionRepository.delete(db, action)

    def remove_listing_with_strike(
        self,
        db: Session,
        admin_id: uuid.UUID,
        listing_id: uuid.UUID,
        reason: str | None,
    ) -> AdminAction:
        """
        Remove a listing and issue a strike to the owner.

        This is the complete business logic for listing removal:
        1. Validate listing exists and get owner
        2. Create LISTING_REMOVAL action for audit trail
        3. Issue STRIKE to listing owner (triggers auto-ban if threshold reached)
        4. Hard delete the listing from database

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            listing_id: Listing ID being removed
            reason: Reason for removal

        Returns:
            AdminAction: The LISTING_REMOVAL action (strike is created internally)

        Raises:
            HTTPException: If listing not found
        """
        listing = ListingRepository.get_by_id(db, listing_id)
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing {listing_id} not found",
            )

        seller_id = listing.seller_id

        removal_action = AdminActionCreate(
            target_user_id=seller_id,
            target_listing_id=listing_id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason=reason,
            expires_at=None,
        )
        listing_removal = AdminActionRepository.create(db, admin_id, removal_action)

        self.create_strike(
            db=db,
            admin_id=admin_id,
            target_user_id=seller_id,
            strike=AdminActionStrike(reason=f"Listing removed: {reason or 'Policy violation'}"),
        )

        # Import here to avoid circular dependency between services
        from app.services.listing import listing_service  # noqa: PLC0415

        listing_service.delete(db, listing_id, admin_id, UserRole.ADMIN)
        return listing_removal


# Create a singleton instance
admin_action_service = AdminActionService()
