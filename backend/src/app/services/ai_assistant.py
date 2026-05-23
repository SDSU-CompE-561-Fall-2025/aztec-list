"""
AI assistant service.

Drives one chat turn: persists the user message, runs the RAG graph, streams
answer tokens as Server-Sent Events, and persists the assistant message with its
cited sources.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage

from app.core.enums import AIMessageRole
from app.core.llm import get_chat_model
from app.repository.ai_conversation import AIConversationRepository
from app.services import rag

if TYPE_CHECKING:
    import uuid
    from collections.abc import AsyncIterator

    from langchain_core.messages import BaseMessage
    from sqlalchemy.orm import Session

    from app.models.ai_conversation import AIConversation
    from app.models.user import User
    from app.schemas.ai import AIChatRequest

logger = logging.getLogger(__name__)


def _sse(payload: dict[str, object]) -> str:
    """Format a payload as a Server-Sent Event line."""
    return f"data: {json.dumps(payload)}\n\n"


def _history_to_messages(conversation: AIConversation) -> list[BaseMessage]:
    """Convert stored conversation turns into LangChain messages."""
    messages: list[BaseMessage] = []
    for msg in conversation.messages:
        if msg.role == AIMessageRole.USER:
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    return messages


def _cited_sources(answer: str, grounding: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep only the grounding listings whose title is mentioned in the answer."""
    lowered = answer.lower()
    return [source for source in grounding if source["title"].lower() in lowered]


class AIAssistantService:
    """Orchestrates a single streamed assistant turn."""

    async def stream_chat(
        self, db: Session, user: User, request: AIChatRequest
    ) -> AsyncIterator[str]:
        """Yield SSE lines: start -> sources -> token* -> done (or error)."""
        conversation = self._resolve_conversation(db, user.id, request.conversation_id)
        history = _history_to_messages(conversation)

        # Persist the user's message before answering.
        AIConversationRepository.add_message(
            db, conversation.id, AIMessageRole.USER, request.message
        )
        yield _sse({"type": "start", "conversation_id": str(conversation.id)})

        # Carry the recent turn into retrieval so follow-ups ("any others?") keep the topic.
        prior_user = [m.content for m in history if isinstance(m, HumanMessage)]
        retrieval_query = f"{prior_user[-1]} {request.message}" if prior_user else request.message

        graph = rag.build_graph(db, get_chat_model())
        grounding: list[dict[str, str]] = []
        answer_parts: list[str] = []

        try:
            async for mode, data in graph.astream(
                {
                    "question": request.message,
                    "retrieval_query": retrieval_query,
                    "history": history,
                },
                stream_mode=["updates", "messages"],
            ):
                if mode == "updates" and "retrieve" in data:
                    grounding = data["retrieve"].get("sources", [])
                elif mode == "messages":
                    chunk, meta = data
                    if meta.get("langgraph_node") == "generate" and chunk.content:
                        text = (
                            chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        )
                        answer_parts.append(text)
                        yield _sse({"type": "token", "content": text})
        except Exception:
            logger.exception("AI assistant stream failed")
            yield _sse({"type": "error", "message": "The assistant failed to respond."})
            return

        # Cite only the listings the assistant actually recommended (the LLM is a better
        # relevance judge than cosine on short titles), not the whole grounding set.
        answer = "".join(answer_parts)
        cited = _cited_sources(answer, grounding)
        yield _sse({"type": "sources", "sources": cited})

        message = AIConversationRepository.add_message(
            db,
            conversation.id,
            AIMessageRole.ASSISTANT,
            answer,
            sources=cited or None,
        )
        yield _sse({"type": "done", "message_id": str(message.id)})

    @staticmethod
    def _resolve_conversation(
        db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID | None
    ) -> AIConversation:
        """Continue an owned conversation, or start a new one."""
        if conversation_id is not None:
            existing = AIConversationRepository.get_for_user(db, conversation_id, user_id)
            if existing is not None:
                return existing
        return AIConversationRepository.create(db, user_id)


ai_assistant_service = AIAssistantService()
