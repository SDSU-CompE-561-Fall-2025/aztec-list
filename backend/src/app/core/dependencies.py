from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import oauth2_scheme, verify_token
from app.core.database import get_db
from app.core.security import ensure_admin
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.services.user import user_service

# Optional bearer token scheme (doesn't raise error if missing)
optional_oauth2_scheme = HTTPBearer(auto_error=False)


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


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """
    Optionally get the current authenticated user from JWT token.

    Returns the user if a valid token is provided, or None if no token
    or invalid token. Does not raise an exception for missing/invalid tokens.

    Use this for endpoints that work for both authenticated and guest users.

    Args:
        credentials: Optional JWT access token
        db: Database session

    Returns:
        User | None: Current authenticated user, or None if not authenticated
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        return None

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        return None

    return user_service.get_by_id(db, user_id=user_id)


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


def require_verified_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require that the current user has verified their email address.

    This dependency should be used on endpoints that require email verification,
    such as creating listings or messaging other users.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        User: Current authenticated verified user

    Raises:
        HTTPException: 403 if user has not verified their email
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address to perform this action. Check your inbox for the verification link.",
        )
    return current_user
