"""
Message routes.

This module contains REST endpoints for conversations and messages.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.routes.websocket_messages import websocket_router
from app.schemas.conversation import ConversationCreate, ConversationPublic
from app.schemas.message import MessagePublic
from app.services.conversation import conversation_service
from app.services.message import message_service

message_router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)

# Include WebSocket routes
message_router.include_router(websocket_router)


@message_router.post(
    "/conversations",
    summary="Create or get existing conversation with another user",
    response_model=ConversationPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Conversation:
    """
    Create a new conversation with another user or return existing one.

    Checks if a conversation already exists between the two users (in either order).
    If found, returns the existing conversation. Otherwise, creates a new one.

    Args:
        data: Conversation creation data with other_user_id
        current_user: Authenticated user
        db: Database session

    Returns:
        ConversationPublic: Created or existing conversation

    Raises:
        HTTPException: 404 if other user not found, 400 if trying to message self
    """
    return conversation_service.get_or_create(db, current_user.id, data.other_user_id)


@message_router.get(
    "/conversations",
    summary="Get all conversations for current user",
    response_model=list[ConversationPublic],
    status_code=status.HTTP_200_OK,
)
async def get_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Conversation]:
    """
    Get all conversations where the current user is a participant.

    Returns conversations ordered by creation date (most recent first).

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
    Returns:
        list[ConversationPublic]: List of user's conversations
    """
    return conversation_service.get_user_conversations(db, current_user.id)


@message_router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get messages from a conversation",
    response_model=list[MessagePublic],
    status_code=status.HTTP_200_OK,
)
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum number of messages to return")
    ] = 20,
    skip: Annotated[int, Query(ge=0, description="Number of messages to skip")] = 0,
) -> list[Message]:
    """
    Get messages from a conversation with pagination.

    Returns messages ordered by creation time (oldest first).
    User must be a participant in the conversation to access messages.

    Args:
        conversation_id: Conversation UUID
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of messages (default 20, max 100)
        skip: Number of messages to skip for pagination

    Returns:
        list[MessagePublic]: List of messages

    Raises:
        HTTPException: 404 if conversation not found, 403 if not a participant
    """
    # Verify conversation exists and user is participant
    conversation_service.get_by_id(db, conversation_id)
    conversation_service.verify_participant(db, conversation_id, current_user.id)

    return message_service.get_conversation_messages(db, conversation_id, limit, skip)
