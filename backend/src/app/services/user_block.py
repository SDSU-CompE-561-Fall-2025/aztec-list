"""
User block service.

Business logic for proactive, user-enforced blocking. A block stops the blocked
party from starting a new conversation with, or delivering new messages to, the
blocker. Admins cannot be blocked (they must stay reachable for support), and a user
cannot block themselves.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.enums import UserRole
from app.repository.user import UserRepository
from app.repository.user_block import UserBlockRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.user_block import UserBlock


class UserBlockService:
    """Service for user-block business logic."""

    def block(self, db: Session, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> UserBlock:
        """
        Block ``blocked_id`` on behalf of ``blocker_id``.

        Idempotent: re-blocking an already-blocked user returns the existing row.

        Raises:
            HTTPException: 400 on self-block, 404 if target missing, 403 if target is an admin.
        """
        if blocker_id == blocked_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot block yourself.",
            )

        target = UserRepository.get_by_id(db, blocked_id)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if target.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrators cannot be blocked.",
            )

        existing = UserBlockRepository.get(db, blocker_id, blocked_id)
        if existing is not None:
            return existing

        try:
            block = UserBlockRepository.create_no_commit(db, blocker_id, blocked_id)
            db.commit()
        except Exception:
            db.rollback()
            raise
        else:
            return block

    def unblock(self, db: Session, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> None:
        """Remove a block. Idempotent: unblocking a non-blocked user is a no-op (no error)."""
        existing = UserBlockRepository.get(db, blocker_id, blocked_id)
        if existing is not None:
            UserBlockRepository.delete(db, existing)

    def list_blocks(self, db: Session, blocker_id: uuid.UUID) -> list[dict]:
        """Return the accounts this user has blocked, newest first."""
        pairs = UserBlockRepository.list_for_blocker(db, blocker_id)
        return [
            {
                "blocked_user_id": block.blocked_id,
                "blocked_username": username,
                "created_at": block.created_at,
            }
            for block, username in pairs
        ]

    def is_blocked_either_way(self, db: Session, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
        """Return True if either user has blocked the other."""
        return UserBlockRepository.is_blocked_either_way(db, user_a, user_b)

    def is_blocked(self, db: Session, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> bool:
        """Return True if ``blocker_id`` has blocked ``blocked_id`` (directional)."""
        return UserBlockRepository.is_blocked(db, blocker_id, blocked_id)


# Service instance
user_block_service = UserBlockService()
