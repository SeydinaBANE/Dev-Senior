import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from agents.biz_manager.prompts import SYSTEM_PROMPT
from agents.config import biz_manager_model

_python = sys.executable

mcp_google = MCPServerStdio(_python, args=["-m", "mcp_servers.google_workspace.server"])
mcp_crm = MCPServerStdio(_python, args=["-m", "mcp_servers.crm.server"])
mcp_seo = MCPServerStdio(_python, args=["-m", "mcp_servers.seo.server"])

agent = Agent(
    model=biz_manager_model(),
    system_prompt=SYSTEM_PROMPT,
    mcp_servers=[mcp_google, mcp_crm, mcp_seo],
)
