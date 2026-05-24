"""
Retriever de contexte codebase pour l'agent Dev Senior.

Cherche les extraits de code les plus pertinents dans Qdrant
et les formate pour injection dans le prompt de l'agent.
"""

from memory.embeddings import embed
from memory.shared.memory import retrieve_shared
from memory.store import ensure_collection, get_client

COLLECTION_NAME = "codebase"
DEFAULT_TOP_K = 5
MIN_SCORE = 0.70  # score cosine minimum (0=opposé, 1=identique)


def retrieve_context(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Retourne les extraits de code pertinents pour une requête,
    enrichis du contexte partagé avec Business Manager.

    Retourne une chaîne vide si rien de pertinent n'est trouvé,
    pour éviter d'injecter du bruit dans le prompt.
    """
    ensure_collection(COLLECTION_NAME)
    client = get_client()

    parts: list[str] = []

    info = client.get_collection(COLLECTION_NAME)
    if info.points_count:
        query_vector = embed(query)
        results = client.search(  # type: ignore[attr-defined]
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=MIN_SCORE,
            with_payload=True,
        )
        if results:
            parts.append("--- Contexte codebase pertinent ---")
            for hit in results:
                source = hit.payload.get("source", "inconnu")
                text = hit.payload.get("text", "")
                parts.append(f"\n### {source} (similarité: {hit.score:.0%})\n```\n{text}\n```")
            parts.append("--- Fin du contexte ---")

    shared = retrieve_shared(query)
    if shared:
        parts.append(shared)

    return "\n".join(parts)
