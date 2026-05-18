"""
Embeddings via OpenRouter (text-embedding-3-small, dim=1536).
"""
import os
import httpx

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")


def embed(text: str) -> list[float]:
    """Retourne le vecteur d'embedding d'un texte (dim 1536)."""
    r = httpx.post(
        f"{OPENROUTER_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": EMBED_MODEL, "input": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


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
