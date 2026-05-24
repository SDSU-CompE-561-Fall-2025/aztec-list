"""AI shopping-assistant routes (RAG chat over listings)."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.core.settings import settings
from app.models.ai_conversation import AIConversation
from app.models.user import User
from app.repository.ai_conversation import AIConversationRepository
from app.schemas.ai import (
    AIChatRequest,
    AIConversationPublic,
    AIConversationSummary,
    GenerateDescriptionRequest,
    GenerateDescriptionResponse,
)
from app.services.ai_assistant import ai_assistant_service
from app.services.ai_listing_assist import ai_listing_assist_service

logger = logging.getLogger(__name__)

ai_router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def _ensure_ai_enabled() -> None:
    if not settings.ai.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features are disabled",
        )


@ai_router.post("/chat", summary="Stream a shopping-assistant reply (SSE)")
@limiter.limit("10/minute;100/hour")
async def chat(
    request: Request,  # noqa: ARG001 - required by slowapi for rate limiting
    body: AIChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """
    Answer a shopping question grounded in real listings, streamed as SSE.

    Events (``data: {json}``): start, sources, token (repeated), done | error.
    """
    _ensure_ai_enabled()
    stream = ai_assistant_service.stream_chat(db, current_user, body)
    return StreamingResponse(stream, media_type="text/event-stream")


@ai_router.post(
    "/generate-description",
    summary="Generate a listing description (AI)",
)
@limiter.limit("10/minute;100/hour")
async def generate_description(
    request: Request,  # noqa: ARG001 - required by slowapi for rate limiting
    body: GenerateDescriptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001 - auth gate
) -> GenerateDescriptionResponse:
    """Draft a listing description from the title and any seller-provided details."""
    _ensure_ai_enabled()
    try:
        description = await ai_listing_assist_service.generate_description(body)
    except Exception as exc:
        logger.exception("AI description generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not generate a description right now. Please try again or write your own.",
        ) from exc
    return GenerateDescriptionResponse(description=description)


@ai_router.get(
    "/conversations",
    summary="List the current user's AI conversations",
    response_model=list[AIConversationSummary],
)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AIConversation]:
    """Return the user's AI conversations, most recent first."""
    return AIConversationRepository.list_for_user(db, current_user.id)


@ai_router.get(
    "/conversations/{conversation_id}",
    summary="Get an AI conversation with its messages",
    response_model=AIConversationPublic,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AIConversation:
    """Return a single conversation (owner only) with its full message history."""
    conversation = AIConversationRepository.get_for_user(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation
