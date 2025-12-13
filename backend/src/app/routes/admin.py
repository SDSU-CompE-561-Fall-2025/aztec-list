import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin, require_not_banned
from app.core.rate_limiter import limiter
from app.models.admin import AdminAction
from app.models.user import User
from app.schemas.admin import (
    AdminActionBan,
    AdminActionFilters,
    AdminActionListResponse,
    AdminActionPublic,
    AdminActionStrike,
    AdminActionStrikeResponse,
    AdminListingRemoval,
    AdminListingRemovalResponse,
    AdminUserVerification,
    AdminUserVerificationResponse,
)
from app.services.admin import admin_action_service
from app.services.user import user_service

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin), Depends(require_not_banned)],
)


@admin_router.get(
    "/actions",
    summary="List moderation actions with filters",
)
async def list_admin_actions(
    filters: Annotated[AdminActionFilters, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> AdminActionListResponse:
    """
    List moderation actions with optional filters and pagination.

    **Requires:** Admin privileges

    Args:
        filters: Query parameters for filtering (target_user_id, admin_id, action_type, etc.)
        db: Database session

    Returns:
        AdminActionListResponse: List of admin actions with count

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    actions, count = admin_action_service.get_filtered(db=db, filters=filters)

    return AdminActionListResponse(
        items=[AdminActionPublic(**action) for action in actions],
        next_cursor=None,  # TODO: Implement cursor pagination in the future
        count=count,
    )


@admin_router.get(
    "/actions/{action_id}",
    summary="Get a single admin action",
    response_model=AdminActionPublic,
)
async def get_admin_action(
    action_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Retrieve details of a single admin action by ID.

    **Requires:** Admin privileges

    Args:
        action_id: ID of the admin action to fetch
        db: Database session

    Returns:
        AdminActionPublic: Admin action details

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if action not found
    """
    return admin_action_service.get_by_id(db, action_id)


@admin_router.delete(
    "/actions/{action_id}",
    summary="Revoke an admin action",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute;50/hour")
async def delete_admin_action(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    action_id: uuid.UUID,
    admin: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Revoke an admin action (e.g., lift a ban or undo an accidental strike).

    Rate limit: 10 per minute (burst), 50 per hour (sustained) - generous for admin operations.

    **Requires:** Admin privileges

    **Security:** Admins cannot revoke actions targeting themselves.

    Args:
        request: FastAPI request object (required for rate limiting)
        action_id: ID of the action to revoke
        admin: Authenticated admin user from JWT token
        db: Database session

    Returns:
        None: 204 No Content on success

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin or attempting self-revocation, 404 if action not found
    """
    admin_action_service.delete(db, action_id, admin.id)


@admin_router.post(
    "/users/{user_id}/strike",
    summary="Add a strike to a user",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute;50/hour")
async def strike_user(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user_id: uuid.UUID,
    strike: AdminActionStrike,
    admin: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminActionStrikeResponse:
    """
    Add a strike to a user (convenience wrapper).

    Rate limit: 10 per minute (burst), 50 per hour (sustained) - generous for admin operations.

    **Requires:** Admin privileges

    Args:
        request: FastAPI request object (required for rate limiting)
        user_id: ID of the user to strike
        strike: Strike data with optional reason
        admin: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionStrikeResponse: Strike action with auto-ban info

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    strike_action, strike_count, auto_ban_triggered = admin_action_service.create_strike(
        db, admin.id, user_id, strike
    )
    return AdminActionStrikeResponse(
        strike_action=AdminActionPublic.model_validate(strike_action),
        auto_ban_triggered=auto_ban_triggered,
        strike_count=strike_count,
    )


@admin_router.post(
    "/users/{user_id}/ban",
    summary="Ban a user",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminActionPublic,
)
@limiter.limit("5/minute;20/hour")
async def ban_user(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user_id: uuid.UUID,
    ban: AdminActionBan,
    admin: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Ban a user (temporary via expires_at or permanent if omitted).

    Rate limit: 5 per minute (burst), 20 per hour (sustained) - moderate for sensitive admin action.

    **Requires:** Admin privileges

    Args:
        request: FastAPI request object (required for rate limiting)
        user_id: ID of the user to ban
        ban: Ban data with optional reason and expires_at
        admin: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionPublic: Created ban action

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    return admin_action_service.create_ban(db, admin.id, user_id, ban)


@admin_router.post(
    "/listings/{listing_id}/remove",
    summary="Remove a listing for violating policies",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute;20/hour")
async def remove_listing(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    listing_id: uuid.UUID,
    removal: AdminListingRemoval,
    admin: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminListingRemovalResponse:
    """
    Remove a listing that violates policies (spam, inappropriate content, etc.).

    Rate limit: 5 per minute (burst), 20 per hour (sustained) - moderate for sensitive admin action.

    Creates a listing_removal admin action, issues a strike to the listing owner,
    and hard deletes the listing. The strike counts toward auto-escalation to ban.

    **Requires:** Admin privileges

    Args:
        request: FastAPI request object (required for rate limiting)
        listing_id: ID of the listing to remove
        removal: Removal data with reason
        admin: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminListingRemovalResponse: Contains listing_id, status, and admin_action

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if listing not found
    """
    admin_action = admin_action_service.remove_listing_with_strike(
        db=db,
        admin_id=admin.id,
        listing_id=listing_id,
        reason=removal.reason,
    )

    return AdminListingRemovalResponse(
        listing_id=listing_id,
        status="removed",
        admin_action=AdminActionPublic.model_validate(admin_action),
    )


@admin_router.patch(
    "/users/{user_id}/verification",
    summary="Manually verify or unverify a user",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute;50/hour")
async def update_user_verification(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user_id: uuid.UUID,
    verification: AdminUserVerification,
    admin: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUserVerificationResponse:
    """
    Manually set a user's email verification status.

    Rate limit: 10 per minute (burst), 50 per hour (sustained).

    Allows admins to verify users without requiring email verification
    (useful for support cases, edu email issues, etc.) or to unverify users
    if verification was obtained fraudulently.

    **Requires:** Admin privileges

    Args:
        request: FastAPI request object (required for rate limiting)
        user_id: ID of the user to verify/unverify
        verification: Verification data with is_verified boolean
        admin: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminUserVerificationResponse: Contains user_id, is_verified status, and success message

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    if verification.is_verified:
        user = user_service.verify_user(db, user_id)
        action = "verified"
    else:
        user = user_service.unverify_user(db, user_id)
        action = "unverified"

    return AdminUserVerificationResponse(
        user_id=user_id,
        is_verified=user.is_verified,
        message=f"User {action} successfully by admin {admin.username}",
    )
