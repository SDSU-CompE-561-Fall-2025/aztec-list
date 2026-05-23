"""
LLM provider factory + query helpers.

``get_chat_model()`` returns a LangChain chat model for the configured provider
(Ollama by default, Anthropic optional). ``expand_query()`` uses it to rewrite a
vague search into product keywords for better retrieval. Provider packages are
imported lazily so the rest of the app doesn't load them.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.settings import settings

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

_EXPANSION_PROMPT = (
    "Rewrite this marketplace search as 5-10 product keywords or synonyms that a listing title "
    "or description might contain. Output ONLY the keywords separated by spaces - no punctuation, "
    "numbering, or explanation.\nSearch: {query}"
)


def get_chat_model() -> BaseChatModel:
    """Build the configured chat model (Ollama by default, Anthropic optional)."""
    if settings.llm.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic  # noqa: PLC0415 - deferred heavy import

        return ChatAnthropic(
            model=settings.llm.anthropic_model,
            api_key=settings.llm.anthropic_api_key,
            temperature=settings.llm.temperature,
        )

    from langchain_ollama import ChatOllama  # noqa: PLC0415 - deferred heavy import

    return ChatOllama(
        model=settings.llm.ollama_model,
        base_url=settings.llm.ollama_base_url,
        temperature=settings.llm.temperature,
    )


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
