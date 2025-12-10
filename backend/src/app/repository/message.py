"""
Message repository.

This module provides data access layer for message operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.message import Message

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class MessageRepository:
    """Repository for message data access."""

    @staticmethod
    def get_by_conversation(
        db: Session, conversation_id: uuid.UUID, limit: int = 20, skip: int = 0
    ) -> list[Message]:
        """
        Get messages for a conversation with pagination.

        Returns messages ordered by created_at ascending (oldest first).

        Args:
            db: Database session
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)

        Returns:
            list[Message]: List of messages
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(skip)
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
