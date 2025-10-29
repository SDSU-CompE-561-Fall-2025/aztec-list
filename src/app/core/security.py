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

    from app.models.admin import AdminAction
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
