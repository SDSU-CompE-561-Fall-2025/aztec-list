"""
User block repository.

Data access for the ``user_blocks`` table: create / delete a block, membership
checks used by the conversation gate and the WebSocket send path, and a listing of
who a user has blocked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, or_, select

from app.models.user import User
from app.models.user_block import UserBlock

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class UserBlockRepository:
    """Repository for user-block data access."""

    @staticmethod
    def create_no_commit(db: Session, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> UserBlock:
        """Insert a block (caller commits). Assumes the pair does not already exist."""
        block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
        db.add(block)
        db.flush()
        return block

    @staticmethod
    def get(db: Session, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> UserBlock | None:
        """Return the block row for this directed pair, or None."""
        return db.get(UserBlock, (blocker_id, blocked_id))

    @staticmethod
    def delete(db: Session, block: UserBlock) -> None:
        """Delete a block and commit."""
        db.delete(block)
        db.commit()

    @staticmethod
    def is_blocked(db: Session, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> bool:
        """Return True if ``blocker_id`` has blocked ``blocked_id`` (directional)."""
        query = select(UserBlock.blocker_id).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id,
        )
        return db.scalars(query).first() is not None

    @staticmethod
    def is_blocked_either_way(db: Session, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
        """Return True if either user has blocked the other (used by the conversation gate)."""
        query = select(UserBlock.blocker_id).where(
            or_(
                and_(UserBlock.blocker_id == user_a, UserBlock.blocked_id == user_b),
                and_(UserBlock.blocker_id == user_b, UserBlock.blocked_id == user_a),
            )
        )
        return db.scalars(query).first() is not None

    @staticmethod
    def list_for_blocker(db: Session, blocker_id: uuid.UUID) -> list[tuple[UserBlock, str | None]]:
        """Return (block, blocked_username) pairs for everyone this user has blocked."""
        query = (
            select(UserBlock, User.username)
            .outerjoin(User, UserBlock.blocked_id == User.id)
            .where(UserBlock.blocker_id == blocker_id)
            .order_by(UserBlock.created_at.desc())
        )
        return [(row[0], row[1]) for row in db.execute(query).all()]
