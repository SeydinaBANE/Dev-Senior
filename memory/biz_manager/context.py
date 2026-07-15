"""
Mémoire contextuelle pour l'agent Business Manager.

Stocke et retrouve :
- Profils clients (préférences, historique)
- Campagnes passées et leurs résultats
- Notes de réunions et décisions
- Briefs de contenu
"""

import uuid
from datetime import UTC, datetime

from memory.adapters.qdrant_store import QdrantVectorStore
from memory.embeddings import embed
from memory.ports import PayloadFilter, VectorPoint, VectorStore
from memory.shared.memory import retrieve_shared, save_shared

COLLECTION_NAME = "biz_context"


class BizContextRepository:
    """Logique métier de la mémoire Business Manager, indépendante du backend vectoriel."""

    MIN_SCORE = 0.60

    def __init__(self, store: VectorStore | None = None) -> None:
        self._store = store or QdrantVectorStore()

    def save_note(self, content: str, category: str = "general", tags: str = "") -> str:
        """Sauvegarde une note dans la mémoire Business Manager.

        Returns:
            ID de la note créée.
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
                        "category": category,
                        "tags": tags,
                        "created_at": datetime.now(UTC).isoformat(),
                        "text": content,
                    },
                )
            ],
        )
        return note_id

    def retrieve(self, query: str, top_k: int = 4, category: str | None = None) -> str | None:
        """Retrouve les notes pertinentes pour une requête.

        Args:
            query:    Ce que l'agent cherche à contextualiser.
            top_k:    Nombre max de résultats.
            category: Filtre optionnel par catégorie.

        Returns:
            None si la collection est vide (arrêt immédiat, pas de fallback
            mémoire partagée — comportement historique) ; sinon le bloc de
            contexte formaté, ou "" si aucun résultat au-dessus du seuil.
        """
        self._store.ensure_collection(COLLECTION_NAME)
        if self._store.count(COLLECTION_NAME) == 0:
            return None

        query_filter: PayloadFilter | None = {"category": category} if category else None

        results = self._store.search(
            COLLECTION_NAME,
            embed(query),
            limit=top_k,
            score_threshold=self.MIN_SCORE,
            query_filter=query_filter,
        )

        if not results:
            return ""

        parts = ["--- Contexte mémorisé ---"]
        for hit in results:
            cat = hit.payload.get("category", "")
            date = hit.payload.get("created_at", "")[:10]
            text = hit.payload.get("text", "")
            parts.append(f"\n[{cat} • {date}]\n{text}")
        parts.append("--- Fin du contexte ---")
        return "\n".join(parts)


_repo = BizContextRepository()


def save_note(content: str, category: str = "general", tags: str = "") -> str:
    """Sauvegarde une note dans la mémoire Business Manager.

    Returns:
        ID de la note créée.
    """
    return _repo.save_note(content, category, tags)


def save_interaction(user_message: str, agent_response: str, topic: str = "") -> None:
    """Sauvegarde une interaction agent pour enrichir la mémoire long terme."""
    content = f"Question: {user_message}\nRéponse: {agent_response}"
    save_note(content, category="interaction", tags=topic)
    save_shared(content, source_agent="biz_manager", category="interaction", tags=topic)


def retrieve_context(query: str, top_k: int = 4, category: str | None = None) -> str:
    """
    Retrouve les notes pertinentes pour une requête, enrichies du contexte
    partagé avec Dev Senior.

    Args:
        query:    Ce que l'agent cherche à contextualiser.
        top_k:    Nombre max de résultats.
        category: Filtre optionnel par catégorie.
    """
    context_block = _repo.retrieve(query, top_k, category)
    if context_block is None:
        # Collection biz_context vide : arrêt immédiat, pas de fallback mémoire
        # partagée (comportement historique).
        return ""

    parts: list[str] = []
    if context_block:
        parts.append(context_block)

    shared = retrieve_shared(query)
    if shared:
        parts.append(shared)

    return "\n".join(parts)
