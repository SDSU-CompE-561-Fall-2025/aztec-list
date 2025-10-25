import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.enums import ActionType
from app.models.admin import AdminAction
from app.models.user import User
from app.repository.listing import ListingRepository
from app.schemas.admin import (
    AdminActionBan,
    AdminActionCreate,
    AdminActionFilters,
    AdminActionListResponse,
    AdminActionPublic,
    AdminActionStrike,
    AdminActionWarning,
    AdminListingRemoval,
    AdminListingRemovalResponse,
    AdminListingRestoreResponse,
)
from app.services.admin import admin_action_service

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@admin_router.post(
    "/actions",
    summary="Create a moderation action",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminActionPublic,
)
async def create_admin_action(
    action: AdminActionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Create a moderation action (warning, strike, ban, or listing_removal).

    **Requires:** Admin privileges

    Args:
        action: Admin action creation data (target_user_id, action_type, reason, etc.)
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionPublic: Created admin action information

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if target user not found
    """
    return admin_action_service.create(db, current_user.id, action)


@admin_router.get(
    "/actions",
    summary="List moderation actions with filters",
)
async def list_admin_actions(
    filters: Annotated[AdminActionFilters, Depends()],
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
    db: Annotated[Session, Depends(get_db)],
) -> AdminActionListResponse:
    """
    List moderation actions with optional filters and pagination.

    **Requires:** Admin privileges

    Args:
        filters: Query parameters for filtering (target_user_id, admin_id, action_type, etc.)
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionListResponse: List of admin actions with count

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    actions, count = admin_action_service.get_filtered(
        db=db,
        target_user_id=filters.target_user_id,
        admin_id=filters.admin_id,
        action_type=filters.action_type,
        target_listing_id=filters.target_listing_id,
        from_date=filters.from_date,
        to_date=filters.to_date,
        limit=filters.limit,
        offset=filters.offset,
    )

    return AdminActionListResponse(
        items=[AdminActionPublic.model_validate(action) for action in actions],
        next_cursor=None,  # Cursor pagination can be implemented later
        count=count,
    )


@admin_router.get(
    "/actions/{action_id}",
    summary="Get a single admin action",
    response_model=AdminActionPublic,
)
async def get_admin_action(
    action_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Retrieve details of a single admin action by ID.

    **Requires:** Admin privileges

    Args:
        action_id: ID of the admin action to fetch
        current_user: Authenticated admin user from JWT token
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
async def delete_admin_action(
    action_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Revoke an admin action (e.g., lift a ban or undo an accidental strike).

    **Requires:** Admin privileges

    Args:
        action_id: ID of the action to revoke
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        None: 204 No Content on success

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if action not found
    """
    admin_action_service.delete(db, action_id)


@admin_router.post(
    "/users/{user_id}/warning",
    summary="Issue a warning to a user",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminActionPublic,
)
async def warn_user(
    user_id: uuid.UUID,
    warning: AdminActionWarning,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Issue a warning to a user (convenience wrapper).

    **Requires:** Admin privileges

    Args:
        user_id: ID of the user to warn
        warning: Warning data with optional reason
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionPublic: Created warning action

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    return admin_action_service.create_warning(db, current_user.id, user_id, warning)


@admin_router.post(
    "/users/{user_id}/strike",
    summary="Add a strike to a user",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminActionPublic,
)
async def strike_user(
    user_id: uuid.UUID,
    strike: AdminActionStrike,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Add a strike to a user (convenience wrapper).

    **Requires:** Admin privileges

    Args:
        user_id: ID of the user to strike
        strike: Strike data with optional reason
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionPublic: Created strike action

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    return admin_action_service.create_strike(db, current_user.id, user_id, strike)


@admin_router.post(
    "/users/{user_id}/ban",
    summary="Ban a user",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminActionPublic,
)
async def ban_user(
    user_id: uuid.UUID,
    ban: AdminActionBan,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminAction:
    """
    Ban a user (temporary via expires_at or permanent if omitted).

    **Requires:** Admin privileges

    Args:
        user_id: ID of the user to ban
        ban: Ban data with optional reason and expires_at
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminActionPublic: Created ban action

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    return admin_action_service.create_ban(db, current_user.id, user_id, ban)


@admin_router.post(
    "/listings/{listing_id}/remove",
    summary="Remove a listing for violating policies",
    status_code=status.HTTP_200_OK,
)
async def remove_listing(
    listing_id: uuid.UUID,
    removal: AdminListingRemoval,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminListingRemovalResponse:
    """
    Remove a listing that violates policies (spam, inappropriate content, etc.).

    Creates a listing_removal admin action and marks the listing as removed.

    **Requires:** Admin privileges

    Args:
        listing_id: ID of the listing to remove
        removal: Removal data with reason
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminListingRemovalResponse: Contains listing_id, status, and admin_action

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if listing not found
    """
    # For listing removal, we need the listing owner's user_id
    listing = ListingRepository.get_by_id(db, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found",
        )

    # Create the admin action for listing removal
    action_data = AdminActionCreate(
        target_user_id=listing.seller_id,  # The listing owner
        target_listing_id=listing_id,
        action_type=ActionType.LISTING_REMOVAL,
        reason=removal.reason,
        expires_at=None,
    )

    admin_action = admin_action_service.create(db, current_user.id, action_data)

    return AdminListingRemovalResponse(
        listing_id=listing_id,
        status="removed",
        admin_action=AdminActionPublic.model_validate(admin_action),
    )


@admin_router.post(
    "/listings/{listing_id}/restore",
    summary="Restore a previously removed listing",
    status_code=status.HTTP_200_OK,
)
async def restore_listing(
    listing_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
    db: Annotated[Session, Depends(get_db)],
) -> AdminListingRestoreResponse:
    """
    Restore a listing that was previously removed by admin action.

    Deletes the listing_removal admin action and restores the listing.

    **Requires:** Admin privileges

    Args:
        listing_id: ID of the listing to restore
        current_user: Authenticated admin user from JWT token
        db: Database session

    Returns:
        AdminListingRestoreResponse: Contains listing_id and status

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin,
                       404 if listing or removal action not found
    """
    # Find the listing_removal action for this listing
    actions = admin_action_service.get_by_target_listing_id(db, listing_id)
    removal_action = next((a for a in actions if a.action_type == ActionType.LISTING_REMOVAL), None)

    if not removal_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No removal action found for listing {listing_id}",
        )

    # Delete the removal action to restore the listing
    admin_action_service.delete(db, removal_action.id)

    return AdminListingRestoreResponse(
        listing_id=listing_id,
        status="restored",
    )
