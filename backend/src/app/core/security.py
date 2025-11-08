"""
Security and authorization utilities.

This module contains pure authorization policy functions that enforce
security rules without database dependencies. These can be reused across
services, dependencies, and other parts of the application.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.enums import UserRole

if TYPE_CHECKING:
    from uuid import UUID

    from app.models.user import User


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


def ensure_resource_owner(resource_owner_id: UUID, user_id: UUID, resource_name: str = "resource") -> None:
    """
    Ensure user is the owner of a resource.

    Generic ownership check that can be used for listings, profiles, images, etc.
    Prevents users from modifying resources they don't own.

    Args:
        resource_owner_id: ID of the user who owns the resource
        user_id: ID of the user attempting the action
        resource_name: Name of the resource type for error message (default: "resource")

    Raises:
        HTTPException: 403 if user is not the owner

    Example:
        >>> ensure_resource_owner(listing.seller_id, current_user.id, "listing")
        >>> ensure_resource_owner(profile.user_id, current_user.id, "profile")
    """
    if resource_owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only the owner can modify this {resource_name}",
        )
