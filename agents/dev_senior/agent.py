from pydantic_ai import Agent
from agents.config import dev_senior_model
from agents.dev_senior.prompts import SYSTEM_PROMPT

agent = Agent(
    model=dev_senior_model(),
    system_prompt=SYSTEM_PROMPT,
)
