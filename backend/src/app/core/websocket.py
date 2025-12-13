"""
WebSocket utilities for authentication.

This module contains helper functions for WebSocket authentication.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.auth import verify_token
from app.models.user import User
from app.repository.user import UserRepository


def authenticate_websocket_user(db: Session, token: str) -> User | None:
    """
    Authenticate user from JWT token for WebSocket connections.

    Args:
        db: Database session
        token: JWT access token

    Returns:
        User | None: Authenticated user if token valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        return None

    return UserRepository.get_by_id(db, user_id)
