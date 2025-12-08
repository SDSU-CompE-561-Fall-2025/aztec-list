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
from app.core.storage import delete_listing_images
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
        ban = AdminActionRepository.has_active_ban(db, user_id)
        if ban:
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
    ) -> tuple[list[dict], int]:
        """
        Get admin actions with optional filters and pagination.

        Returns actions as dictionaries with username fields for API serialization.

        Args:
            db: Database session
            filters: Filter criteria and pagination parameters

        Returns:
            tuple[list[dict], int]: Filtered admin actions as dicts and total count
        """
        results = AdminActionRepository.get_filtered(db=db, filters=filters)
        count = AdminActionRepository.count_filtered(db=db, filters=filters)

        # Convert to dictionaries with username fields for API response
        actions_with_usernames = []
        for action, admin_username, target_username in results:
            # Create a dict representation that includes usernames
            action_dict = {
                "id": action.id,
                "admin_id": action.admin_id,
                "admin_username": admin_username,
                "target_user_id": action.target_user_id,
                "target_username": target_username,
                "action_type": action.action_type,
                "reason": action.reason,
                "target_listing_id": action.target_listing_id,
                "created_at": action.created_at,
                "expires_at": action.expires_at,
            }
            actions_with_usernames.append(action_dict)

        return actions_with_usernames, count

    def create_strike(
        self,
        db: Session,
        admin_id: uuid.UUID,
        target_user_id: uuid.UUID,
        strike: AdminActionStrike,
    ) -> tuple[AdminAction, int, bool]:
        """
        Create a strike action with auto-escalation to ban at threshold.

        Automatically issues a permanent ban if user reaches strike threshold.
        Prevents admins from striking other admins and already banned users.
        All operations performed in a single transaction.

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            target_user_id: Target user ID to strike
            strike: Strike data with reason

        Returns:
            tuple[AdminAction, int, bool]: (created_strike, strike_count, auto_ban_triggered)

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

        try:
            created_strike = AdminActionRepository.create_no_commit(db, admin_id, action)

            strike_count = AdminActionRepository.count_strikes(db, target_user_id)
            auto_ban_triggered = False
            if strike_count >= settings.moderation.strike_auto_ban_threshold:
                ban_action = AdminActionCreate(
                    target_user_id=target_user_id,
                    action_type=AdminActionType.BAN,
                    reason=f"Automatic permanent ban: {strike_count} strikes accumulated. Latest: {strike.reason or 'Policy violation'}",
                    target_listing_id=None,
                    expires_at=None,
                )
                AdminActionRepository.create_no_commit(db, admin_id, ban_action)
                auto_ban_triggered = True
            db.commit()

        except Exception:
            db.rollback()
            raise
        else:
            return created_strike, strike_count, auto_ban_triggered

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

        When revoking an auto-ban (from 3 strikes), also removes the most recent strike
        to prevent immediate re-banning. All operations performed in a single transaction.

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

        try:
            is_auto_ban = (
                action.action_type == AdminActionType.BAN
                and action.reason
                and "Automatic permanent ban" in action.reason
                and "strikes accumulated" in action.reason
            )

            if is_auto_ban and action.target_user_id:
                user_actions = AdminActionRepository.get_by_target_user_id(
                    db, action.target_user_id
                )
                strikes = [a for a in user_actions if a.action_type == AdminActionType.STRIKE]
                if strikes:
                    most_recent_strike = strikes[0]
                    AdminActionRepository.delete_no_commit(db, most_recent_strike)

            AdminActionRepository.delete_no_commit(db, action)
            db.commit()

        except Exception:
            db.rollback()
            raise

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
        2. Issue STRIKE to listing owner ONLY if not already banned
           - If not banned, strike may trigger auto-ban if threshold reached
           - If already banned, skip strike (cleanup without additional penalty)
        3. Hard delete the listing from database
        4. All database operations are performed in a single transaction

        Args:
            db: Database session
            admin_id: Admin user ID performing the action
            listing_id: Listing ID being removed
            reason: Reason for removal

        Returns:
            AdminAction: The LISTING_REMOVAL action audit record for the removed listing.

        Raises:
            HTTPException: If listing not found or listing is owned by an admin
        """
        listing = ListingRepository.get_by_id(db, listing_id)
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing {listing_id} not found",
            )

        seller_id = listing.seller_id

        seller = UserRepository.get_by_id(db, seller_id)
        if seller and seller.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove a listing posted by an admin",
            )

        try:
            ListingRepository.delete_no_commit(db, listing)

            removal_action = AdminActionCreate(
                target_user_id=seller_id,
                action_type=AdminActionType.LISTING_REMOVAL,
                reason=reason or "Policy violation",
                target_listing_id=listing_id,
                expires_at=None,
            )
            removal_record = AdminActionRepository.create_no_commit(db, admin_id, removal_action)

            if AdminActionRepository.has_active_ban(db, seller_id) is None:
                strike_action = AdminActionCreate(
                    target_user_id=seller_id,
                    action_type=AdminActionType.STRIKE,
                    reason=f"Listing removed: {reason or 'Policy violation'}",
                    target_listing_id=None,
                    expires_at=None,
                )
                AdminActionRepository.create_no_commit(db, admin_id, strike_action)

                strike_count = AdminActionRepository.count_strikes(db, seller_id)
                if strike_count >= settings.moderation.strike_auto_ban_threshold:
                    ban_action = AdminActionCreate(
                        target_user_id=seller_id,
                        action_type=AdminActionType.BAN,
                        reason=f"Automatic permanent ban: {strike_count} strikes accumulated. Latest: {reason or 'Policy violation'}",
                        target_listing_id=None,
                        expires_at=None,
                    )
                    AdminActionRepository.create_no_commit(db, admin_id, ban_action)
            db.commit()

        except Exception:
            db.rollback()
            raise
        else:
            delete_listing_images(listing_id)

            return removal_record


# Create a singleton instance
admin_action_service = AdminActionService()
