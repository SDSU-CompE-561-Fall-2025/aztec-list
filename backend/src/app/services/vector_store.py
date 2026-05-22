"""
Vector store service.

Stores and searches listing embeddings in Qdrant. Two deployment modes:

- **Embedded (default for local dev):** an on-disk Qdrant at ``VECTOR__PATH``.
  Single-process only - fine for a dev server, not for concurrent workers.
- **Server (Docker / production):** a remote Qdrant set via ``VECTOR__QDRANT_URL``.

The Qdrant client is created lazily so importing this module is cheap when AI
features are disabled.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from qdrant_client import QdrantClient, models

from app.core.settings import settings
from app.services.embeddings import embedding_service

if TYPE_CHECKING:
    from decimal import Decimal

    from app.core.enums import Category, Condition
    from app.models.listing import Listing
    from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


def _enum_value(value: object) -> object:
    """Return the underlying value of an Enum, or the value itself if not an Enum."""
    return value.value if isinstance(value, Enum) else value


@dataclass(frozen=True)
class ListingFilter:
    """Structural filters applied alongside a semantic query (mirrors search params)."""

    category: Category | None = None
    condition: Condition | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    seller_id: uuid.UUID | None = None
    active_only: bool = True


class VectorStoreService:
    """Listing embedding storage and semantic search backed by Qdrant."""

    def __init__(
        self,
        *,
        location: str | None = None,
        collection: str | None = None,
        embedder: EmbeddingService | None = None,
    ) -> None:
        # `location` overrides settings (used by tests, e.g. ":memory:").
        self._location = location
        self._collection = collection or settings.vector.collection
        self._embedder = embedder or embedding_service
        self._client: QdrantClient | None = None

    def _make_client(self) -> QdrantClient:
        if self._location is not None:
            return QdrantClient(location=self._location)
        if settings.vector.qdrant_url:
            return QdrantClient(url=settings.vector.qdrant_url)
        return QdrantClient(path=settings.vector.path)

    @property
    def client(self) -> QdrantClient:
        """Lazily-created Qdrant client."""
        if self._client is None:
            self._client = self._make_client()
        return self._client

    def ensure_collection(self) -> None:
        """Create the listings collection if it does not already exist."""
        if self.client.collection_exists(self._collection):
            return
        self.client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(
                size=self._embedder.dimension,
                distance=models.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection %s", self._collection)

    def upsert_listing(self, listing: Listing) -> None:
        """Embed a listing and upsert its vector + filterable payload."""
        vector = self._embedder.embed_listing(listing.title, listing.description)
        self.client.upsert(
            collection_name=self._collection,
            points=[
                models.PointStruct(
                    id=str(listing.id),
                    vector=vector,
                    payload={
                        "category": _enum_value(listing.category),
                        "condition": _enum_value(listing.condition),
                        "price": float(listing.price),
                        "seller_id": str(listing.seller_id),
                        "is_active": bool(listing.is_active),
                    },
                )
            ],
        )

    def delete_listing(self, listing_id: uuid.UUID) -> None:
        """Remove a listing's vector from the collection."""
        self.client.delete(
            collection_name=self._collection,
            points_selector=models.PointIdsList(points=[str(listing_id)]),
        )

    def _build_filter(self, listing_filter: ListingFilter | None) -> models.Filter | None:
        listing_filter = listing_filter or ListingFilter()
        conditions: list[models.FieldCondition] = []

        if listing_filter.active_only:
            conditions.append(
                models.FieldCondition(key="is_active", match=models.MatchValue(value=True))
            )
        if listing_filter.category is not None:
            conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=_enum_value(listing_filter.category)),
                )
            )
        if listing_filter.condition is not None:
            conditions.append(
                models.FieldCondition(
                    key="condition",
                    match=models.MatchValue(value=_enum_value(listing_filter.condition)),
                )
            )
        if listing_filter.seller_id is not None:
            conditions.append(
                models.FieldCondition(
                    key="seller_id",
                    match=models.MatchValue(value=str(listing_filter.seller_id)),
                )
            )
        if listing_filter.min_price is not None or listing_filter.max_price is not None:
            conditions.append(
                models.FieldCondition(
                    key="price",
                    range=models.Range(
                        gte=float(listing_filter.min_price)
                        if listing_filter.min_price is not None
                        else None,
                        lte=float(listing_filter.max_price)
                        if listing_filter.max_price is not None
                        else None,
                    ),
                )
            )

        return models.Filter(must=conditions) if conditions else None

    def search(
        self,
        query_text: str,
        *,
        limit: int,
        score_threshold: float | None = None,
        listing_filter: ListingFilter | None = None,
    ) -> list[tuple[uuid.UUID, float]]:
        """
        Return (listing_id, score) tuples ranked by similarity, best first.

        Only points scoring at least ``score_threshold`` (cosine) are returned, so
        irrelevant listings are dropped instead of merely ranked lower.
        """
        query_vector = self._embedder.embed_query(query_text)
        response = self.client.query_points(
            collection_name=self._collection,
            query=query_vector,
            query_filter=self._build_filter(listing_filter),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=False,
        )
        return [(uuid.UUID(str(point.id)), point.score) for point in response.points]

    def count(self, listing_filter: ListingFilter | None = None) -> int:
        """Count listings matching the structural filters (ignores the query vector)."""
        return self.client.count(
            collection_name=self._collection,
            count_filter=self._build_filter(listing_filter),
            exact=True,
        ).count

    def reset_collection(self) -> None:
        """Drop and recreate the collection - clears stale/orphan vectors before a full rebuild."""
        if self.client.collection_exists(self._collection):
            self.client.delete_collection(self._collection)
        self.ensure_collection()

    def close(self) -> None:
        """Close the Qdrant client, releasing the embedded on-disk lock if held."""
        if self._client is not None:
            self._client.close()
            self._client = None


# Module-level singleton (Qdrant client + embedding model both load lazily).
vector_store = VectorStoreService()
