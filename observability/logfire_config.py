# Redirige vers Langfuse — gardé pour compatibilité des imports existants.
from observability.langfuse_config import configure_observability as configure_logfire

__all__ = ["configure_logfire"]
