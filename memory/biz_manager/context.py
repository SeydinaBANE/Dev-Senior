"""
Mémoire contextuelle pour l'agent Business Manager.

Stocke et retrouve :
- Profils clients (préférences, historique)
- Campagnes passées et leurs résultats
- Notes de réunions et décisions
- Briefs de contenu
"""
import uuid
from datetime import datetime, timezone

from memory.store import get_or_create_collection
from memory.embeddings import embed

COLLECTION_NAME = "biz_context"


def _collection():
    return get_or_create_collection(COLLECTION_NAME)


# ── Écriture ──────────────────────────────────────────────────────────────────

def save_note(content: str, category: str = "general", tags: str = "") -> str:
    """Sauvegarde une note dans la mémoire Business Manager.

    Args:
        content:  Contenu de la note.
        category: Catégorie ('client', 'campaign', 'meeting', 'brief', 'general').
        tags:     Mots-clés séparés par des virgules.

    Returns:
        ID de la note créée.
    """
    note_id = str(uuid.uuid4())
    embedding = embed(content)
    _collection().add(
        ids=[note_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{
            "category": category,
            "tags": tags,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }],
    )
    return note_id


def save_interaction(user_message: str, agent_response: str, topic: str = "") -> None:
    """Sauvegarde une interaction agent pour enrichir la mémoire long terme."""
    content = f"Question: {user_message}\nRéponse: {agent_response}"
    save_note(content, category="interaction", tags=topic)


# ── Lecture ───────────────────────────────────────────────────────────────────

def retrieve_context(query: str, top_k: int = 4, category: str | None = None) -> str:
    """
    Retrouve les notes pertinentes pour une requête.

    Args:
        query:    Ce que l'agent cherche à contextualiser.
        top_k:    Nombre max de résultats.
        category: Filtre optionnel par catégorie.
    """
    col = _collection()
    if col.count() == 0:
        return ""

    query_embedding = embed(query)
    where = {"category": category} if category else None

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, col.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    relevant = [
        (doc, meta, dist)
        for doc, meta, dist in zip(docs, metas, distances)
        if dist <= 0.4
    ]

    if not relevant:
        return ""

    parts = ["--- Contexte mémorisé ---"]
    for doc, meta, _ in relevant:
        cat = meta.get("category", "")
        date = meta.get("created_at", "")[:10]
        parts.append(f"\n[{cat} • {date}]\n{doc}")
    parts.append("--- Fin du contexte ---")

    return "\n".join(parts)
