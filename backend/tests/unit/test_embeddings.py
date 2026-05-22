"""Smoke test for the real fastembed embedding service.

Marked `slow` because it downloads the embedding model on first run. Run with:

    uv run pytest tests/unit/test_embeddings.py
    uv run pytest -m "not slow"   # to skip it
"""

import pytest

from app.services.embeddings import EmbeddingService

EXPECTED_DIM = 384  # BAAI/bge-small-en-v1.5


@pytest.mark.slow
def test_embedding_dimension_and_determinism() -> None:
    service = EmbeddingService()

    vector_a = service.embed_query("a wooden study desk")
    vector_b = service.embed_query("a wooden study desk")

    assert len(vector_a) == service.dimension == EXPECTED_DIM
    assert vector_a == vector_b  # same text -> identical vector


@pytest.mark.slow
def test_related_text_more_similar_than_unrelated() -> None:
    service = EmbeddingService()

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
        return dot / norm

    query = service.embed_query("desk for studying")
    related = service.embed_listing("Wooden study desk", "great for a dorm room")
    unrelated = service.embed_listing("Mountain bike", "21-speed, lightly used")

    assert cosine(query, related) > cosine(query, unrelated)
