"""
Construction de l'agent Dev Senior (pydantic-ai) — l'adapter concret du port AgentPort.
"""

import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from agents.config import dev_senior_model
from agents.dev_senior.prompts import SYSTEM_PROMPT
from agents.ports import AgentPort


def build_agent() -> AgentPort:
    python = sys.executable
    mcp_github = MCPServerStdio(python, args=["-m", "mcp_servers.github.server"])
    return Agent(
        model=dev_senior_model(),
        system_prompt=SYSTEM_PROMPT,
        mcp_servers=[mcp_github],
    )
