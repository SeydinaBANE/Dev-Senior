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

from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from memory.store import get_client, ensure_collection
from memory.embeddings import embed

COLLECTION_NAME = "biz_context"
MIN_SCORE = 0.60


def _ensure() -> None:
    ensure_collection(COLLECTION_NAME)


# ── Écriture ──────────────────────────────────────────────────────────────────

def save_note(content: str, category: str = "general", tags: str = "") -> str:
    """Sauvegarde une note dans la mémoire Business Manager.

    Returns:
        ID de la note créée.
    """
    _ensure()
    note_id = str(uuid.uuid4())
    # Qdrant IDs must be UUID or integer — use UUID string directly
    point_id = note_id
    embedding = embed(content)
    get_client().upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "category": category,
                    "tags": tags,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "text": content,
                },
            )
        ],
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
    _ensure()
    client = get_client()
    info = client.get_collection(COLLECTION_NAME)
    if info.points_count == 0:
        return ""

    query_vector = embed(query)
    query_filter = None
    if category:
        query_filter = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
        )

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=MIN_SCORE,
        query_filter=query_filter,
        with_payload=True,
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
