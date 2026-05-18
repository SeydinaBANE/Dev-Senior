from pydantic_ai import Agent
from agents.config import biz_manager_model
from agents.biz_manager.prompts import SYSTEM_PROMPT

agent = Agent(
    model=biz_manager_model(),
    system_prompt=SYSTEM_PROMPT,
)
