"""
Configuration Langfuse — tracing pour tous les agents.

Appeler configure_observability() au démarrage.
get_langfuse() retourne None si les clés ne sont pas configurées (tracing désactivé).
"""
import os
from langfuse import Langfuse

_langfuse: Langfuse | None = None


def get_langfuse() -> Langfuse | None:
    """Retourne le singleton Langfuse, ou None si les clés sont absentes."""
    global _langfuse
    if _langfuse is None:
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        if not public_key or not secret_key:
            return None
        _langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    return _langfuse


def configure_observability(service_name: str) -> None:
    """Initialise Langfuse. Silencieux si les clés ne sont pas configurées."""
    lf = get_langfuse()
    if lf:
        # Vérifie la connexion sans bloquer
        try:
            lf.flush()
        except Exception:
            pass
    _ = service_name  # utilisé comme metadata dans les traces individuelles


def flush() -> None:
    """Force l'envoi des traces en attente (appeler au shutdown)."""
    if _langfuse is not None:
        try:
            _langfuse.flush()
        except Exception:
            pass
