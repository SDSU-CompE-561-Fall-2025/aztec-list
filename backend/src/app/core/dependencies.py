from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import oauth2_scheme, verify_token
from app.core.database import get_db
from app.core.security import ensure_admin
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.services.user import user_service


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get the current authenticated user from JWT token.

    Fetches and validates the full User object from the database.
    This is the standard authentication dependency used across all protected endpoints.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception from None

    user = user_service.get_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require that the current user has admin role.

    This dependency should be used on admin-only routes to enforce
    role-based access control.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        User: Current authenticated admin user

    Raises:
        HTTPException: 403 if user does not have admin role
    """
    ensure_admin(current_user)
    return current_user


def require_not_banned(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Require that the current user is not banned.

    Checks for active BAN admin actions against the user. This dependency should
    be used on mutation endpoints (POST, PUT, PATCH, DELETE) to prevent banned
    users from creating or modifying content.

    Args:
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        User: Current authenticated user (not banned)

    Raises:
        HTTPException: 403 if user has an active ban
    """
    ban = AdminActionRepository.has_active_ban(db, current_user.id)
    if ban:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account banned. Contact support for assistance.",
        )
    return current_user
