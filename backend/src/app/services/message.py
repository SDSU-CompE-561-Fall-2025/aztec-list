"""
Message service.

This module contains business logic for message operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.repository.message import MessageRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.message import Message


class MessageService:
    """Service for message business logic."""

    def get_conversation_messages(
        self, db: Session, conversation_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Message]:
        """
        Get messages for a conversation with pagination.

        Returns messages ordered by creation time (oldest first).

        Args:
            db: Database session
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip for pagination

        Returns:
            list[Message]: List of messages
        """
        return MessageRepository.get_by_conversation(db, conversation_id, limit, offset)

    def create(
        self, db: Session, conversation_id: uuid.UUID, sender_id: uuid.UUID, content: str
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
        return MessageRepository.create(db, conversation_id, sender_id, content)


# Service instance
message_service = MessageService()
