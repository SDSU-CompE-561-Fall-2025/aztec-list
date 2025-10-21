from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import oauth2_scheme, verify_token
from app.core.database import get_db
from app.models.user import User
from app.services.user import user_service


def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UUID:
    """
    Extract and validate user ID from JWT token without database lookup.

    Useful when you only need the user_id for authorization checks
    or queries, and don't need the full User object.

    Args:
        token: JWT access token

    Returns:
        UUID: Current user's ID

    Raises:
        HTTPException: If token is invalid or missing user_id
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
        return UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception from None


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get the current authenticated user from JWT token.

    Fetches the full User object from database. Use get_current_user_id() instead
    if you only need the user_id to avoid unnecessary database queries.

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
