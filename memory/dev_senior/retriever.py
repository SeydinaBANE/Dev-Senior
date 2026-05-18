"""
Retriever de contexte codebase pour l'agent Dev Senior.

Cherche les extraits de code les plus pertinents dans Qdrant
et les formate pour injection dans le prompt de l'agent.
"""
from memory.store import get_client, ensure_collection
from memory.embeddings import embed

COLLECTION_NAME = "codebase"
DEFAULT_TOP_K = 5
MIN_SCORE = 0.70  # score cosine minimum (0=opposé, 1=identique)


def retrieve_context(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Retourne les extraits de code pertinents pour une requête.

    Retourne une chaîne vide si rien de pertinent n'est trouvé,
    pour éviter d'injecter du bruit dans le prompt.
    """
    ensure_collection(COLLECTION_NAME)
    client = get_client()

    info = client.get_collection(COLLECTION_NAME)
    if info.points_count == 0:
        return ""

    query_vector = embed(query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=MIN_SCORE,
        with_payload=True,
    )

    if not results:
        return ""

    parts = ["--- Contexte codebase pertinent ---"]
    for hit in results:
        source = hit.payload.get("source", "inconnu")
        text = hit.payload.get("text", "")
        parts.append(f"\n### {source} (similarité: {hit.score:.0%})\n```\n{text}\n```")
    parts.append("--- Fin du contexte ---")

    return "\n".join(parts)
