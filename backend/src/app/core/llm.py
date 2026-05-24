"""
LLM provider factory + query helpers.

``get_chat_model()`` returns the chat model for the shopping assistant (provider from
``LLM__PROVIDER``). ``get_assist_model()`` / ``get_structured_model()`` build the model for
the newer assist and moderation features, which can target a different provider via
``LLM__ASSIST_PROVIDER`` (so Claude can power those while the assistant stays local).
``expand_query()`` rewrites a vague search into product keywords for better retrieval.
Provider packages are imported lazily so the rest of the app doesn't load them.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.settings import settings

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.runnables import Runnable
    from pydantic import BaseModel

logger = logging.getLogger(__name__)

_EXPANSION_PROMPT = (
    "Rewrite this marketplace search as 5-10 product keywords or synonyms that a listing title "
    "or description might contain. Output ONLY the keywords separated by spaces - no punctuation, "
    "numbering, or explanation.\nSearch: {query}"
)


def _build_chat_model(provider: str, *, temperature: float | None = None) -> BaseChatModel:
    """Build a chat model for the given provider (Ollama by default, Anthropic optional)."""
    temp = settings.llm.temperature if temperature is None else temperature
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic  # noqa: PLC0415 - deferred heavy import

        return ChatAnthropic(
            model=settings.llm.anthropic_model,
            api_key=settings.llm.anthropic_api_key,
            temperature=temp,
        )

    from langchain_ollama import ChatOllama  # noqa: PLC0415 - deferred heavy import

    return ChatOllama(
        model=settings.llm.ollama_model,
        base_url=settings.llm.ollama_base_url,
        temperature=temp,
        # Disable Qwen3.x "thinking" mode: we want fast, direct output, not hidden chain-of-thought
        # that stalls streaming and pollutes one-shot responses. Harmless on non-reasoning models.
        reasoning=False,
    )


def get_chat_model() -> BaseChatModel:
    """Build the assistant chat model (provider from ``LLM__PROVIDER``)."""
    return _build_chat_model(settings.llm.provider)


def get_assist_model(*, temperature: float | None = None) -> BaseChatModel:
    """
    Build the chat model for assist and moderation features.

    Uses ``LLM__ASSIST_PROVIDER`` when set, otherwise the global ``LLM__PROVIDER`` - so Claude
    can power these tasks while the chat assistant stays on a local model.
    """
    provider = settings.llm.assist_provider or settings.llm.provider
    return _build_chat_model(provider, temperature=temperature)


def get_structured_model[SchemaT: BaseModel](
    schema: type[SchemaT],
) -> Runnable[LanguageModelInput, SchemaT]:
    """Return an assist model that emits validated ``schema`` instances (structured output)."""
    return get_assist_model().with_structured_output(schema)


def get_vision_model() -> BaseChatModel:
    """Build a vision-capable chat model (Claude) for image understanding and moderation."""
    from langchain_anthropic import ChatAnthropic  # noqa: PLC0415 - deferred heavy import

    return ChatAnthropic(
        model=settings.llm.anthropic_model,
        api_key=settings.llm.anthropic_api_key,
        temperature=settings.llm.temperature,
    )


def get_structured_vision_model[SchemaT: BaseModel](
    schema: type[SchemaT],
) -> Runnable[LanguageModelInput, SchemaT]:
    """Return a vision model that emits validated ``schema`` instances (image classification)."""
    return get_vision_model().with_structured_output(schema)


def expand_query(query: str) -> str:
    """
    Expand a vague query into product keywords for better embedding recall.

    Returns the original query unchanged when expansion is disabled or the LLM is
    unavailable, so semantic search never hard-depends on the LLM being up.
    """
    if not settings.llm.expand_queries or not query.strip():
        return query
    try:
        response = get_chat_model().invoke(_EXPANSION_PROMPT.format(query=query))
        content = response.content
        keywords = (content if isinstance(content, str) else str(content)).strip()
    except Exception:
        logger.exception("Query expansion failed; using the raw query")
        return query
    return f"{query} {keywords}" if keywords else query
