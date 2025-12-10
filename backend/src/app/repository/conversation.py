"""
Conversation repository.

This module provides data access layer for conversation operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from app.models.conversation import Conversation

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class ConversationRepository:
    """Repository for conversation data access."""

    @staticmethod
    def get_by_id(db: Session, conversation_id: uuid.UUID) -> Conversation | None:
        """
        Get conversation by ID with user data eagerly loaded.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Conversation | None: Conversation if found, None otherwise
        """
        query = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(joinedload(Conversation.user_1), joinedload(Conversation.user_2))
        )
        return db.scalars(query).first()

    @staticmethod
    def get_by_participants(
        db: Session, user_1_id: uuid.UUID, user_2_id: uuid.UUID
    ) -> Conversation | None:
        """
        Get conversation by two participant IDs, checking both orderings.

        Args:
            db: Database session
            user_1_id: First user UUID
            user_2_id: Second user UUID

        Returns:
            Conversation | None: Conversation if found, None otherwise
        """
        query = (
            select(Conversation)
            .where(
                or_(
                    (Conversation.user_1_id == user_1_id) & (Conversation.user_2_id == user_2_id),
                    (Conversation.user_1_id == user_2_id) & (Conversation.user_2_id == user_1_id),
                )
            )
            .options(joinedload(Conversation.user_1), joinedload(Conversation.user_2))
        )
        return db.scalars(query).first()

    @staticmethod
    def get_user_conversations(db: Session, user_id: uuid.UUID) -> list[Conversation]:
        """
        Get all conversations for a user where they are either participant.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            list[Conversation]: List of conversations
        """
        query = (
            select(Conversation)
            .where(or_(Conversation.user_1_id == user_id, Conversation.user_2_id == user_id))
            .options(joinedload(Conversation.user_1), joinedload(Conversation.user_2))
            .order_by(Conversation.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def create(db: Session, user_1_id: uuid.UUID, user_2_id: uuid.UUID) -> Conversation:
        """
        Create a new conversation between two users.

        Args:
            db: Database session
            user_1_id: First user UUID
            user_2_id: Second user UUID

        Returns:
            Conversation: Created conversation
        """
        conversation = Conversation(user_1_id=user_1_id, user_2_id=user_2_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def is_participant(db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Check if a user is a participant in a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Returns:
            bool: True if user is participant, False otherwise
        """
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            or_(Conversation.user_1_id == user_id, Conversation.user_2_id == user_id),
        )
        return db.scalars(query).first() is not None
