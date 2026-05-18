"""
Configuration Logfire — tracing pour tous les agents.

Appeler configure_logfire() au démarrage de chaque agent.
Instrumente automatiquement Pydantic AI, httpx et les appels LLM.
"""
import os
import logfire


def configure_logfire(service_name: str) -> None:
    """Initialise Logfire pour un agent donné.

    Args:
        service_name: Nom du service ('dev-senior' ou 'biz-manager').
    """
    token = os.getenv("LOGFIRE_TOKEN")

    logfire.configure(
        token=token,
        service_name=service_name,
        service_version=os.getenv("APP_VERSION", "0.1.0"),
        # En l'absence de token, logfire reste actif localement (console)
        send_to_logfire=bool(token),
    )

    # Instrumentation automatique
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx()
