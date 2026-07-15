"""
Registry des agents — remplace les singletons module-level dev_agent/biz_agent
pour l'API FastAPI. Attaché à app.state.agents dans le lifespan, même pattern
que app.state.sessions (api/sessions.py::SessionStore.create()).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agents.adapters.biz_manager_agent import build_agent as build_biz_manager_agent
from agents.adapters.dev_senior_agent import build_agent as build_dev_senior_agent
from agents.ports import AgentPort


class AgentRegistry:
    def __init__(self, dev_senior: AgentPort, biz_manager: AgentPort) -> None:
        self.dev_senior = dev_senior
        self.biz_manager = biz_manager

    @classmethod
    def create(cls) -> "AgentRegistry":
        return cls(dev_senior=build_dev_senior_agent(), biz_manager=build_biz_manager_agent())

    def get(self, name: str) -> AgentPort:
        return self.dev_senior if name == "dev-senior" else self.biz_manager

    @asynccontextmanager
    async def run_mcp_servers(self) -> AsyncIterator[None]:
        async with self.dev_senior.run_mcp_servers():
            async with self.biz_manager.run_mcp_servers():
                yield
