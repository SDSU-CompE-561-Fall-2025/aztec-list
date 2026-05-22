"""
Embedding service.

Wraps a local fastembed text-embedding model (no API key, runs offline) used to
turn listing text and search queries into vectors for semantic search.

The model is loaded lazily on first use so that importing this module - and
running the app with AI features disabled - costs nothing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.settings import settings

if TYPE_CHECKING:
    from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


def listing_to_text(title: str, description: str) -> str:
    """Combine listing fields into a single document string for embedding."""
    return f"{title}\n{description}"


class EmbeddingService:
    """Lazily-loaded local text-embedding model (fastembed)."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.embedding.model
        self._model: TextEmbedding | None = None
        self._dimension: int | None = None

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            from fastembed import TextEmbedding  # noqa: PLC0415 - deferred heavy import

            logger.info("Loading embedding model %s", self._model_name)
            self._model = TextEmbedding(model_name=self._model_name)
        return self._model

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query (uses the model's query-side formatting)."""
        vector = next(iter(self._get_model().query_embed(text)))
        return vector.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents (listing text)."""
        return [vector.tolist() for vector in self._get_model().passage_embed(texts)]

    def embed_listing(self, title: str, description: str) -> list[float]:
        """Embed a single listing's combined title + description."""
        return self.embed_documents([listing_to_text(title, description)])[0]

    @property
    def dimension(self) -> int:
        """Vector dimension produced by the model (probed once, then cached)."""
        if self._dimension is None:
            self._dimension = len(self.embed_query("dimension probe"))
        return self._dimension


# Module-level singleton (model still loads lazily on first embed call).
embedding_service = EmbeddingService()
