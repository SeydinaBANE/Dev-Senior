"""
Port pour les agents conversationnels. pydantic_ai.Agent satisfait déjà cette
interface structurellement — un seul backend aujourd'hui, donc pas de classe
wrapper : le port sert à typer les call-sites (routes, lifespan) indépendamment
du framework concret.
"""

from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol, runtime_checkable

from pydantic_ai.messages import ModelMessage


@runtime_checkable
class AgentPort(Protocol):
    """Interface satisfaite par pydantic_ai.Agent — mêmes méthodes que celles
    utilisées aujourd'hui par les routes et le lifespan FastAPI."""

    async def run(
        self,
        user_prompt: str,
        *,
        message_history: list[ModelMessage] | None = None,
    ) -> Any: ...

    def run_stream(
        self,
        user_prompt: str,
        *,
        message_history: list[ModelMessage] | None = None,
    ) -> AbstractAsyncContextManager[Any]: ...

    def run_mcp_servers(self) -> AbstractAsyncContextManager[None]: ...
