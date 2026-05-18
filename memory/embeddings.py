"""
Embeddings via Ollama (nomic-embed-text).
Utilisé pour indexer et requêter ChromaDB.
"""
import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


def embed(text: str) -> list[float]:
    """Retourne le vecteur d'embedding d'un texte."""
    r = httpx.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Retourne les embeddings de plusieurs textes."""
    return [embed(t) for t in texts]


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Découpe un texte en chunks avec overlap pour préserver le contexte."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
