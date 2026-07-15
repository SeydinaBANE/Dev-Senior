"""
Mémoire partagée entre Dev Senior et Business Manager.

Collection Qdrant "shared" — chaque point porte un champ source_agent
("dev_senior" | "biz_manager") pour tracer l'origine de l'information.

API publique :
- save_shared    : écrire une information dans le pool partagé
- retrieve_shared: lire les informations pertinentes depuis le pool partagé
"""

import uuid
from datetime import UTC, datetime

from memory.adapters.qdrant_store import QdrantVectorStore
from memory.embeddings import embed
from memory.ports import PayloadFilter, VectorPoint, VectorStore

COLLECTION_NAME = "shared"


class SharedMemoryRepository:
    """Logique métier de la mémoire partagée, indépendante du backend vectoriel."""

    MIN_SCORE = 0.65

    def __init__(self, store: VectorStore | None = None) -> None:
        self._store = store or QdrantVectorStore()

    def save(
        self,
        content: str,
        source_agent: str,
        category: str = "general",
        tags: str = "",
    ) -> str:
        """Sauvegarde une information dans la mémoire partagée.

        Returns:
            ID UUID du point créé.
        """
        self._store.ensure_collection(COLLECTION_NAME)
        note_id = str(uuid.uuid4())
        self._store.upsert(
            COLLECTION_NAME,
            [
                VectorPoint(
                    id=note_id,
                    vector=embed(content),
                    payload={
                        "source_agent": source_agent,
                        "category": category,
                        "tags": tags,
                        "created_at": datetime.now(UTC).isoformat(),
                        "text": content,
                    },
                )
            ],
        )
        return note_id

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        source_agent: str | None = None,
    ) -> str:
        """Retrouve les informations partagées pertinentes pour une requête.

        Returns:
            Contexte formaté prêt à être injecté dans un prompt, ou "" si vide.
        """
        self._store.ensure_collection(COLLECTION_NAME)
        if self._store.count(COLLECTION_NAME) == 0:
            return ""

        query_filter: PayloadFilter | None = (
            {"source_agent": source_agent} if source_agent else None
        )

        results = self._store.search(
            COLLECTION_NAME,
            embed(query),
            limit=top_k,
            score_threshold=self.MIN_SCORE,
            query_filter=query_filter,
        )

        if not results:
            return ""

        parts = ["--- Contexte partagé ---"]
        for hit in results:
            agent = hit.payload.get("source_agent", "")
            cat = hit.payload.get("category", "")
            date = hit.payload.get("created_at", "")[:10]
            text = hit.payload.get("text", "")
            parts.append(f"\n[{agent} • {cat} • {date}]\n{text}")
        parts.append("--- Fin du contexte partagé ---")

        return "\n".join(parts)


_repo = SharedMemoryRepository()


def save_shared(
    content: str,
    source_agent: str,
    category: str = "general",
    tags: str = "",
) -> str:
    """Sauvegarde une information dans la mémoire partagée.

    Args:
        content:      Texte à mémoriser.
        source_agent: Agent émetteur — "dev_senior" ou "biz_manager".
        category:     Catégorie libre (ex: "decision", "client", "deadline").
        tags:         Mots-clés séparés par des virgules.

    Returns:
        ID UUID du point créé.
    """
    return _repo.save(content, source_agent, category, tags)


def retrieve_shared(
    query: str,
    top_k: int = 3,
    source_agent: str | None = None,
) -> str:
    """Retrouve les informations partagées pertinentes pour une requête.

    Args:
        query:        Requête pour la recherche sémantique.
        top_k:        Nombre max de résultats.
        source_agent: Filtre optionnel sur l'agent source.

    Returns:
        Contexte formaté prêt à être injecté dans un prompt, ou "" si vide.
    """
    return _repo.retrieve(query, top_k, source_agent)
