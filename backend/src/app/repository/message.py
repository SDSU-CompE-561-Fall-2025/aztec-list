"""
Message repository.

This module provides data access layer for message operations.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - used in a runtime return annotation
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.models.message import Message

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class MessageRepository:
    """Repository for message data access."""

    @staticmethod
    def get_by_id(db: Session, message_id: uuid.UUID) -> Message | None:
        """Fetch a single message by id, or None if it does not exist."""
        return db.get(Message, message_id)

    @staticmethod
    def get_latest_message_map(
        db: Session, conversation_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[str, datetime]]:
        """
        Return the newest message per conversation as ``{id: (content, created_at)}``.

        Uses a single window-function query (row_number over each conversation, newest
        first) so building an inbox preview never becomes an N+1 of per-conversation
        lookups. Conversations with no messages are simply absent from the map.
        """
        if not conversation_ids:
            return {}
        row_number = (
            func.row_number()
            .over(
                partition_by=Message.conversation_id,
                order_by=(Message.created_at.desc(), Message.id.desc()),
            )
            .label("rn")
        )
        ranked = (
            select(
                Message.conversation_id.label("conversation_id"),
                Message.content.label("content"),
                Message.created_at.label("created_at"),
                row_number,
            )
            .where(Message.conversation_id.in_(conversation_ids))
            .subquery()
        )
        query = select(ranked.c.conversation_id, ranked.c.content, ranked.c.created_at).where(
            ranked.c.rn == 1
        )
        return {row[0]: (row[1], row[2]) for row in db.execute(query).all()}

    @staticmethod
    def get_by_conversation(
        db: Session, conversation_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Message]:
        """
        Get messages for a conversation with pagination.

        Returns messages ordered by created_at ascending (oldest first).

        Args:
            db: Database session
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip (for pagination)

        Returns:
            list[Message]: List of messages
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(query).all())

    @staticmethod
    def create(
        db: Session, conversation_id: uuid.UUID, sender_id: uuid.UUID, content: str
    ) -> Message:
        """
        Create a new message in a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            sender_id: Sender user UUID
            content: Message text content

        Returns:
            Message: Created message
        """
        message = Message(conversation_id=conversation_id, sender_id=sender_id, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
