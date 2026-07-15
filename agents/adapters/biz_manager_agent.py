"""
Construction de l'agent Business Manager (pydantic-ai) — l'adapter concret du port AgentPort.
"""

import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from agents.biz_manager.prompts import SYSTEM_PROMPT
from agents.config import biz_manager_model
from agents.ports import AgentPort


def build_agent() -> AgentPort:
    python = sys.executable
    mcp_google = MCPServerStdio(python, args=["-m", "mcp_servers.google_workspace.server"])
    mcp_crm = MCPServerStdio(python, args=["-m", "mcp_servers.crm.server"])
    mcp_seo = MCPServerStdio(python, args=["-m", "mcp_servers.seo.server"])
    return Agent(
        model=biz_manager_model(),
        system_prompt=SYSTEM_PROMPT,
        mcp_servers=[mcp_google, mcp_crm, mcp_seo],
    )
