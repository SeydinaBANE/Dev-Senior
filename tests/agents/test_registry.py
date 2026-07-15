"""
Tests du registry d'agents — remplace les singletons module-level dev_agent/biz_agent.
"""

from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

import pytest

from agents.registry import AgentRegistry


def _fake_agent(name: str) -> MagicMock:
    agent = MagicMock(name=name)
    calls: list[str] = []

    @asynccontextmanager
    async def run_mcp_servers():  # type: ignore[no-untyped-def]
        calls.append(f"{name}:enter")
        yield
        calls.append(f"{name}:exit")

    agent.run_mcp_servers.side_effect = run_mcp_servers
    agent._calls = calls
    return agent


def test_get_returns_dev_senior_for_dev_senior_name() -> None:
    dev = _fake_agent("dev")
    biz = _fake_agent("biz")
    registry = AgentRegistry(dev_senior=dev, biz_manager=biz)

    assert registry.get("dev-senior") is dev


def test_get_returns_biz_manager_for_anything_else() -> None:
    dev = _fake_agent("dev")
    biz = _fake_agent("biz")
    registry = AgentRegistry(dev_senior=dev, biz_manager=biz)

    assert registry.get("biz-manager") is biz
    assert registry.get("whatever") is biz


@pytest.mark.asyncio
async def test_run_mcp_servers_nests_dev_senior_before_biz_manager() -> None:
    dev = _fake_agent("dev")
    biz = _fake_agent("biz")
    registry = AgentRegistry(dev_senior=dev, biz_manager=biz)

    order: list[str] = []
    async with registry.run_mcp_servers():
        order.append("inside")

    assert dev._calls == ["dev:enter", "dev:exit"]
    assert biz._calls == ["biz:enter", "biz:exit"]


def test_create_builds_both_agents_via_factories() -> None:
    with (
        patch("agents.registry.build_dev_senior_agent", return_value="dev-agent"),
        patch("agents.registry.build_biz_manager_agent", return_value="biz-agent"),
    ):
        registry = AgentRegistry.create()

    assert registry.dev_senior == "dev-agent"
    assert registry.biz_manager == "biz-agent"
