import sys
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from agents.config import dev_senior_model
from agents.dev_senior.prompts import SYSTEM_PROMPT

_python = sys.executable

mcp_github = MCPServerStdio(_python, args=["-m", "mcp_servers.github.server"])

agent = Agent(
    model=dev_senior_model(),
    system_prompt=SYSTEM_PROMPT,
    mcp_servers=[mcp_github],
)
