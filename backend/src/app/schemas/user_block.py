"""
User block schemas.

Pydantic models for the "block / unblock user" flow and the authenticated
user's list of accounts they have blocked.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserBlockPublic(BaseModel):
    """One block the current user has placed."""

    blocked_user_id: uuid.UUID
    blocked_username: str | None = None
    created_at: datetime


class UserBlockListResponse(BaseModel):
    """All accounts the current user has blocked."""

    items: list[UserBlockPublic]
    count: int
