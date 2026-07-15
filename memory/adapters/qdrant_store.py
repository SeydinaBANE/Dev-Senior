"""
Adapter Qdrant pour le port VectorStore.

Seul fichier (avec memory/store.py) autorisé à importer qdrant_client /
qdrant_client.models — tous les autres modules de memory/ passent par le port.
"""

from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from memory.ports import EMBEDDING_DIM, PayloadFilter, VectorHit, VectorPoint, VectorStore
from memory.store import get_client


def _to_filter(f: PayloadFilter | None) -> Filter | None:
    if not f:
        return None
    return Filter(must=[FieldCondition(key=k, match=MatchValue(value=v)) for k, v in f.items()])


def _to_id(point_id: int | str | UUID) -> int | str:
    """qdrant-client peut renvoyer un UUID pour un id str — normalisé en str."""
    return point_id if isinstance(point_id, int | str) else str(point_id)


class QdrantVectorStore(VectorStore):
    """Wrappe le client Qdrant partagé (memory.store.get_client()), ou un client
    injecté (tests / autre instance)."""

    def __init__(self, client: QdrantClient | None = None) -> None:
        self._client = client or get_client()

    def ensure_collection(self, name: str, size: int = EMBEDDING_DIM) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if name not in existing:
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )

    def count(self, name: str) -> int:
        return self._client.get_collection(name).points_count or 0

    def upsert(self, name: str, points: list[VectorPoint]) -> None:
        self._client.upsert(
            collection_name=name,
            points=[PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points],
        )

    def search(
        self,
        name: str,
        query_vector: list[float],
        *,
        limit: int,
        score_threshold: float | None = None,
        query_filter: PayloadFilter | None = None,
    ) -> list[VectorHit]:
        response = self._client.query_points(
            collection_name=name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=_to_filter(query_filter),
            with_payload=True,
        )
        return [
            VectorHit(id=_to_id(r.id), payload=r.payload or {}, score=r.score)
            for r in response.points
        ]

    def scroll(self, name: str, *, filter: PayloadFilter, limit: int) -> list[VectorHit]:
        points, _ = self._client.scroll(
            collection_name=name,
            scroll_filter=_to_filter(filter),
            limit=limit,
            with_payload=True,
        )
        return [VectorHit(id=_to_id(p.id), payload=p.payload or {}) for p in points]

    def delete(self, name: str, *, filter: PayloadFilter) -> None:
        qfilter = _to_filter(filter)
        assert qfilter is not None, "delete() requiert un filtre non vide"
        self._client.delete(
            collection_name=name,
            points_selector=FilterSelector(filter=qfilter),
        )
