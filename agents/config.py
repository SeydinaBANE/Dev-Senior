import os
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIModel

load_dotenv()

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def openrouter_model(model: str) -> OpenAIModel:
    """Retourne un modèle via OpenRouter (API OpenAI-compatible)."""
    return OpenAIModel(
        model,
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )


def dev_senior_model() -> OpenAIModel:
    model = os.getenv("DEV_SENIOR_MODEL", "qwen/qwen-2.5-coder-7b-instruct")
    return openrouter_model(model)


def biz_manager_model() -> OpenAIModel:
    model = os.getenv("BIZ_MANAGER_MODEL", "meta-llama/llama-3.1-8b-instruct")
    return openrouter_model(model)
