"""
Mémoire partagée entre Dev Senior et Business Manager.

Collection Qdrant "shared" — chaque point porte un champ source_agent
("dev_senior" | "biz_manager") pour tracer l'origine de l'information.

API publique :
- save_shared    : écrire une information dans le pool partagé
- retrieve_shared: lire les informations pertinentes depuis le pool partagé
"""
import uuid
from datetime import datetime, timezone

from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from memory.store import get_client, ensure_collection
from memory.embeddings import embed

COLLECTION_NAME = "shared"
MIN_SCORE = 0.65


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
    ensure_collection(COLLECTION_NAME)
    note_id = str(uuid.uuid4())
    get_client().upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=note_id,
                vector=embed(content),
                payload={
                    "source_agent": source_agent,
                    "category": category,
                    "tags": tags,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "text": content,
                },
            )
        ],
    )
    return note_id


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
    ensure_collection(COLLECTION_NAME)
    client = get_client()
    if client.get_collection(COLLECTION_NAME).points_count == 0:
        return ""

    query_filter = None
    if source_agent:
        query_filter = Filter(
            must=[FieldCondition(key="source_agent", match=MatchValue(value=source_agent))]
        )

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embed(query),
        limit=top_k,
        score_threshold=MIN_SCORE,
        query_filter=query_filter,
        with_payload=True,
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
