"""
Tests de smoke : vérifient que les agents s'initialisent correctement.
Pas d'appel réseau — utilise TestModel de Pydantic AI.
"""

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from agents.biz_manager.prompts import SYSTEM_PROMPT as BIZ_PROMPT
from agents.dev_senior.prompts import SYSTEM_PROMPT as DEV_PROMPT


@pytest.fixture
def dev_agent() -> Agent:
    return Agent(model=TestModel(), system_prompt=DEV_PROMPT)


@pytest.fixture
def biz_agent() -> Agent:
    return Agent(model=TestModel(), system_prompt=BIZ_PROMPT)


async def test_dev_senior_responds(dev_agent: Agent) -> None:
    result = await dev_agent.run("Bonjour, qui es-tu ?")
    assert result.data is not None


async def test_biz_manager_responds(biz_agent: Agent) -> None:
    result = await biz_agent.run("Bonjour, qui es-tu ?")
    assert result.data is not None


def test_dev_prompt_not_empty() -> None:
    assert len(DEV_PROMPT) > 100


def test_biz_prompt_not_empty() -> None:
    assert len(BIZ_PROMPT) > 100
