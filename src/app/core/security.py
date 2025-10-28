"""
Security and authorization utilities.

This module contains pure authorization policy functions that enforce
security rules without database dependencies. These can be reused across
services, dependencies, and other parts of the application.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.enums import AdminActionType, UserRole

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from app.models.admin import AdminAction
    from app.models.listing import Listing
    from app.models.user import User


def ensure_not_banned(actions: Sequence[AdminAction]) -> None:
    """
    Ensure user does not have an active ban.

    Pure authorization policy function that checks a collection of admin actions
    for any BAN entries.

    Args:
        actions: Sequence of admin actions to check

    Raises:
        HTTPException: 403 if any BAN action is found
    """
    for action in actions:
        if action.action_type == AdminActionType.BAN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account banned. Contact support for assistance.",
            )


def ensure_admin(user: User) -> None:
    """
    Ensure user has admin role.

    Pure authorization policy function that checks if a user has admin privileges.

    Args:
        user: User to check for admin role

    Raises:
        HTTPException: 403 if user does not have admin role
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


def ensure_owner_or_admin(
    resource_owner_id: UUID, requesting_user_id: UUID, user_role: UserRole
) -> None:
    """
    Ensure user is the resource owner or an admin.

    Pure authorization policy for resource ownership checks. Used for
    operations like updating/deleting listings, profiles, etc.

    Args:
        resource_owner_id: ID of the user who owns the resource
        requesting_user_id: ID of the user making the request
        user_role: Role of the requesting user

    Raises:
        HTTPException: 403 if user is neither owner nor admin
    """
    if user_role != UserRole.ADMIN and resource_owner_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this resource",
        )


def ensure_listing_owner_or_admin(listing: Listing, user_id: UUID, user_role: UserRole) -> None:
    """
    Ensure user is the listing owner or an admin.

    Convenience wrapper around ensure_owner_or_admin specifically for listings.

    Args:
        listing: Listing object to check ownership of
        user_id: ID of the user making the request
        user_role: Role of the requesting user

    Raises:
        HTTPException: 403 if user is neither owner nor admin
    """
    ensure_owner_or_admin(listing.seller_id, user_id, user_role)


def ensure_verified(user: User) -> None:
    """
    Ensure user account is verified.

    Pure authorization policy that checks if a user's email is verified.
    Can be used to restrict certain actions to verified users only.

    Args:
        user: User to check verification status

    Raises:
        HTTPException: 403 if user is not verified
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required for this action",
        )


def ensure_can_moderate_user(target_user: User, moderator_user: User) -> None:
    """
    Ensure moderator can take action against target user.

    Prevents admins from banning/moderating other admins. Only regular users can be moderated.

    Args:
        target_user: User being moderated (banned, warned, etc.)
        moderator_user: Admin user performing the moderation action

    Raises:
        HTTPException: 403 if target is an admin or moderator lacks privileges
    """
    ensure_admin(moderator_user)

    if target_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot moderate admin accounts. Contact system administrator.",
        )
