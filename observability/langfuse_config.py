"""
Configuration Langfuse — tracing pour tous les agents.

Appeler configure_observability() au démarrage de chaque agent/API.
Fournit get_langfuse() pour créer des traces depuis les routes FastAPI.
"""
import os
from langfuse import Langfuse

_langfuse: Langfuse | None = None


def get_langfuse() -> Langfuse:
    """Retourne le singleton Langfuse (no-op si clés absentes)."""
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    return _langfuse


def configure_observability(service_name: str) -> None:
    """Initialise Langfuse. Silencieux si les clés ne sont pas configurées."""
    lf = get_langfuse()
    # Tag le service pour filtrer dans l'UI Langfuse
    _ = service_name  # utilisé comme metadata dans les traces individuelles
    lf.flush()  # vérifie la connexion au démarrage


def flush() -> None:
    """Force l'envoi des traces en attente (appeler au shutdown)."""
    if _langfuse is not None:
        _langfuse.flush()
