"""
Port pour la mémoire vectorielle (Qdrant aujourd'hui, potentiellement un autre
backend demain). Isole la logique métier (seuils de score, filtres, formatage)
des appels qdrant_client bruts, qui restent confinés à memory/adapters/qdrant_store.py.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from memory.store import EMBEDDING_DIM as EMBEDDING_DIM

# Filtre d'égalité, clés combinées en ET — couvre tous les filtres actuels
# (source, source_agent, category).
PayloadFilter = dict[str, str]


@dataclass(frozen=True)
class VectorPoint:
    id: int | str
    vector: list[float]
    payload: dict[str, Any]


@dataclass(frozen=True)
class VectorHit:
    id: int | str
    payload: dict[str, Any]
    score: float | None = None  # None pour les résultats de scroll() (pas de similarité)


class VectorStore(ABC):
    """Port implémenté par QdrantVectorStore (memory/adapters/qdrant_store.py)."""

    @abstractmethod
    def ensure_collection(self, name: str, size: int = EMBEDDING_DIM) -> None: ...

    @abstractmethod
    def count(self, name: str) -> int: ...

    @abstractmethod
    def upsert(self, name: str, points: list[VectorPoint]) -> None: ...

    @abstractmethod
    def search(
        self,
        name: str,
        query_vector: list[float],
        *,
        limit: int,
        score_threshold: float | None = None,
        query_filter: PayloadFilter | None = None,
    ) -> list[VectorHit]: ...

    @abstractmethod
    def scroll(self, name: str, *, filter: PayloadFilter, limit: int) -> list[VectorHit]: ...

    @abstractmethod
    def delete(self, name: str, *, filter: PayloadFilter) -> None: ...
