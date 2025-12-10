"""
Conversation service.

This module contains business logic for conversation operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.repository.conversation import ConversationRepository
from app.repository.user import UserRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.conversation import Conversation


class ConversationService:
    """Service for conversation business logic."""

    def get_by_id(self, db: Session, conversation_id: uuid.UUID) -> Conversation:
        """
        Get conversation by ID with validation.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Conversation: Conversation object

        Raises:
            HTTPException: If conversation not found
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return conversation

    def get_or_create(
        self, db: Session, current_user_id: uuid.UUID, other_user_id: uuid.UUID
    ) -> Conversation:
        """
        Get existing conversation or create new one between two users.

        Validates that both users exist and prevents self-conversation.
        Checks for existing conversation in both orderings before creating.

        Args:
            db: Database session
            current_user_id: Current authenticated user UUID
            other_user_id: Other user UUID

        Returns:
            Conversation: Existing or newly created conversation

        Raises:
            HTTPException: 404 if other user not found, 400 if trying to message self
        """
        # Validate other user exists
        other_user = UserRepository.get_by_id(db, other_user_id)
        if other_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent self-conversation
        if current_user_id == other_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create conversation with yourself",
            )

        # Check if conversation already exists
        existing_conversation = ConversationRepository.get_by_participants(
            db, current_user_id, other_user_id
        )
        if existing_conversation is not None:
            return existing_conversation

        # Create new conversation
        return ConversationRepository.create(db, current_user_id, other_user_id)

    def get_user_conversations(self, db: Session, user_id: uuid.UUID) -> list[Conversation]:
        """
        Get all conversations for a user.

        Returns conversations ordered by creation date (most recent first).

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            list[Conversation]: List of user's conversations
        """
        return ConversationRepository.get_user_conversations(db, user_id)

    def verify_participant(
        self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """
        Verify that a user is a participant in a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Raises:
            HTTPException: 403 if user is not a participant
        """
        if not ConversationRepository.is_participant(db, conversation_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )


# Service instance
conversation_service = ConversationService()
