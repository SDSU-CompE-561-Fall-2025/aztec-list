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
        Get conversation by two participant IDs.

        Uses normalized user ordering (smaller UUID first) to match the
        unique constraint and ensure consistent lookups.

        Args:
            db: Database session
            user_1_id: First user UUID
            user_2_id: Second user UUID

        Returns:
            Conversation | None: Conversation if found, None otherwise
        """
        # Normalize user ordering to match unique constraint
        normalized_user_1 = min(user_1_id, user_2_id)
        normalized_user_2 = max(user_1_id, user_2_id)

        query = (
            select(Conversation)
            .where(
                (Conversation.user_1_id == normalized_user_1)
                & (Conversation.user_2_id == normalized_user_2)
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

        Normalizes user IDs to ensure consistent ordering (smaller UUID first)
        for unique constraint compatibility.

        Args:
            db: Database session
            user_1_id: First user UUID
            user_2_id: Second user UUID

        Returns:
            Conversation: Created conversation
        """
        # Normalize user ordering for unique constraint
        normalized_user_1 = min(user_1_id, user_2_id)
        normalized_user_2 = max(user_1_id, user_2_id)

        conversation = Conversation(user_1_id=normalized_user_1, user_2_id=normalized_user_2)
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
