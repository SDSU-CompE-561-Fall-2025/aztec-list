"""
Conversation service.

This module contains business logic for conversation operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository
from app.repository.user import UserRepository
from app.services.user_block import user_block_service

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

        # Block gate: neither party may start a DM if either has blocked the other.
        # Generic message so a blocked user is not told they were blocked.
        if user_block_service.is_blocked_either_way(db, current_user_id, other_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can no longer message this user.",
            )

        # Check if conversation already exists
        existing_conversation = ConversationRepository.get_by_participants(
            db, current_user_id, other_user_id
        )
        if existing_conversation is not None:
            return existing_conversation

        # Create new conversation with race condition handling
        try:
            return ConversationRepository.create(db, current_user_id, other_user_id)
        except IntegrityError:
            # Race condition: another request created it between check and insert
            # Rollback and re-query
            db.rollback()
            existing_conversation = ConversationRepository.get_by_participants(
                db, current_user_id, other_user_id
            )
            if existing_conversation is not None:
                return existing_conversation
            # If still not found, something else went wrong
            raise

    def get_user_conversations(self, db: Session, user_id: uuid.UUID) -> list[dict]:
        """
        Get all conversations for a user, each with a last-message preview.

        Conversations are newest-first. Threads the current user has blocked the other
        party in are hidden (the blocked party still sees the thread; only the blocker
        hides it). Each item carries ``last_message`` / ``last_message_at`` for the
        inbox preview, or None when the conversation has no messages yet.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            list[dict]: Conversation fields plus the last-message preview.
        """
        conversations = ConversationRepository.get_user_conversations(db, user_id)
        visible = [
            conv
            for conv in conversations
            if not user_block_service.is_blocked(
                db,
                user_id,
                conv.user_2_id if conv.user_1_id == user_id else conv.user_1_id,
            )
        ]

        latest = MessageRepository.get_latest_message_map(db, [conv.id for conv in visible])
        result = []
        for conv in visible:
            preview = latest.get(conv.id)
            result.append(
                {
                    "id": conv.id,
                    "user_1_id": conv.user_1_id,
                    "user_2_id": conv.user_2_id,
                    "created_at": conv.created_at,
                    "last_message": preview[0] if preview else None,
                    "last_message_at": preview[1] if preview else None,
                }
            )
        return result

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
