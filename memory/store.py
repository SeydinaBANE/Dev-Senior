"""
Client ChromaDB partagé entre tous les agents.
"""
import os
import chromadb
from chromadb import HttpClient

_client: HttpClient | None = None


def get_client() -> HttpClient:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000")),
            headers={"Authorization": f"Bearer {os.getenv('CHROMA_TOKEN', 'dev-token')}"},
        )
    return _client


def get_or_create_collection(name: str, metadata: dict | None = None) -> chromadb.Collection:
    return get_client().get_or_create_collection(
        name=name,
        metadata=metadata or {"hnsw:space": "cosine"},
    )
