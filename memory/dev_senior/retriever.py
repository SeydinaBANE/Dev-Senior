"""
Retriever de contexte codebase pour l'agent Dev Senior.

Cherche les extraits de code les plus pertinents dans ChromaDB
et les formate pour injection dans le prompt de l'agent.
"""
from memory.store import get_or_create_collection
from memory.embeddings import embed

COLLECTION_NAME = "codebase"
DEFAULT_TOP_K = 5
MIN_RELEVANCE = 0.3  # distance cosine max (0 = identique, 1 = opposé)


def retrieve_context(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Retourne les extraits de code pertinents pour une requête.

    Retourne une chaîne vide si rien de pertinent n'est trouvé,
    pour éviter d'injecter du bruit dans le prompt.
    """
    collection = get_or_create_collection(COLLECTION_NAME)

    if collection.count() == 0:
        return ""

    query_embedding = embed(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    relevant = [
        (doc, meta, dist)
        for doc, meta, dist in zip(docs, metas, distances)
        if dist <= MIN_RELEVANCE
    ]

    if not relevant:
        return ""

    parts = ["--- Contexte codebase pertinent ---"]
    for doc, meta, dist in relevant:
        source = meta.get("source", "inconnu")
        parts.append(f"\n### {source} (similarité: {1 - dist:.0%})\n```\n{doc}\n```")
    parts.append("--- Fin du contexte ---")

    return "\n".join(parts)
