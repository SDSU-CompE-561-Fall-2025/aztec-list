"""Data access for AI assistant conversations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation, AIMessage

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.core.enums import AIMessageRole


class AIConversationRepository:
    """Repository for AI conversations and their messages."""

    @staticmethod
    def create(db: Session, user_id: uuid.UUID) -> AIConversation:
        """Start a new conversation for a user."""
        conversation = AIConversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_for_user(
        db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> AIConversation | None:
        """Get a conversation (with messages) only if it belongs to the user."""
        return db.scalar(
            select(AIConversation)
            .where(AIConversation.id == conversation_id, AIConversation.user_id == user_id)
            .options(selectinload(AIConversation.messages))
        )

    @staticmethod
    def list_for_user(db: Session, user_id: uuid.UUID) -> list[AIConversation]:
        """List a user's conversations, most recent first."""
        return list(
            db.scalars(
                select(AIConversation)
                .where(AIConversation.user_id == user_id)
                .order_by(AIConversation.created_at.desc())
            )
        )

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: uuid.UUID,
        role: AIMessageRole,
        content: str,
        sources: list[dict[str, str]] | None = None,
    ) -> AIMessage:
        """Append a message to a conversation."""
        message = AIMessage(
            ai_conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
