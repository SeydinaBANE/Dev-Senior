"""
Retriever de contexte codebase pour l'agent Dev Senior.

Cherche les extraits de code les plus pertinents dans Qdrant
et les formate pour injection dans le prompt de l'agent.
"""

from memory.adapters.qdrant_store import QdrantVectorStore
from memory.embeddings import embed
from memory.ports import VectorPoint, VectorStore
from memory.shared.memory import retrieve_shared

COLLECTION_NAME = "codebase"
DEFAULT_TOP_K = 5


class CodebaseRepository:
    """Logique métier du contexte codebase, indépendante du backend vectoriel.

    Porte aussi les méthodes utilisées par l'indexeur (memory/dev_senior/indexer.py) :
    existing_hash/delete_file/upsert_chunks — même repository, même collection.
    """

    MIN_SCORE = 0.70  # score cosine minimum (0=opposé, 1=identique)

    def __init__(self, store: VectorStore | None = None) -> None:
        self._store = store or QdrantVectorStore()

    def ensure(self) -> None:
        self._store.ensure_collection(COLLECTION_NAME)

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> str:
        """Retourne le bloc de contexte codebase pertinent, ou "" si rien trouvé."""
        self.ensure()
        if self._store.count(COLLECTION_NAME) == 0:
            return ""

        results = self._store.search(
            COLLECTION_NAME,
            embed(query),
            limit=top_k,
            score_threshold=self.MIN_SCORE,
        )
        if not results:
            return ""

        parts = ["--- Contexte codebase pertinent ---"]
        for hit in results:
            source = hit.payload.get("source", "inconnu")
            text = hit.payload.get("text", "")
            score = hit.score or 0.0
            parts.append(f"\n### {source} (similarité: {score:.0%})\n```\n{text}\n```")
        parts.append("--- Fin du contexte ---")
        return "\n".join(parts)

    # ── Support indexeur ───────────────────────────────────────────────────────

    def existing_hash(self, rel_path: str) -> str | None:
        """Retourne le hash stocké pour ce fichier, ou None si absent."""
        hits = self._store.scroll(COLLECTION_NAME, filter={"source": rel_path}, limit=1)
        if hits:
            return hits[0].payload.get("hash")
        return None

    def delete_file(self, rel_path: str) -> None:
        """Supprime tous les chunks indexés pour ce fichier."""
        self._store.delete(COLLECTION_NAME, filter={"source": rel_path})

    def upsert_chunks(self, points: list[VectorPoint]) -> None:
        self._store.upsert(COLLECTION_NAME, points)


_repo = CodebaseRepository()


def retrieve_context(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Retourne les extraits de code pertinents pour une requête,
    enrichis du contexte partagé avec Business Manager.

    Retourne une chaîne vide si rien de pertinent n'est trouvé,
    pour éviter d'injecter du bruit dans le prompt.
    """
    parts: list[str] = []

    codebase_block = _repo.retrieve(query, top_k)
    if codebase_block:
        parts.append(codebase_block)

    shared = retrieve_shared(query)
    if shared:
        parts.append(shared)

    return "\n".join(parts)
