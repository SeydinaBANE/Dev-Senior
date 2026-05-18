import os
from dotenv import load_dotenv
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def ollama_model(model_name: str) -> OpenAIModel:
    """Retourne un modèle Ollama via l'API OpenAI-compatible."""
    return OpenAIModel(
        model_name,
        base_url=f"{OLLAMA_BASE_URL}/v1",
        api_key="ollama",  # Ollama n'a pas besoin de vraie clé
    )


def claude_model(model_name: str | None = None) -> AnthropicModel:
    """Retourne un modèle Claude (Anthropic API)."""
    return AnthropicModel(model_name or "claude-sonnet-4-6")


def dev_senior_model() -> OpenAIModel | AnthropicModel:
    local = os.getenv("DEV_SENIOR_MODEL", "qwen2.5-coder:7b")
    cloud = os.getenv("DEV_SENIOR_MODEL_CLOUD", "claude-sonnet-4-6")
    use_cloud = os.getenv("USE_CLOUD", "false").lower() == "true"
    return claude_model(cloud) if use_cloud else ollama_model(local)


def biz_manager_model() -> OpenAIModel | AnthropicModel:
    local = os.getenv("BIZ_MANAGER_MODEL", "llama3.1:8b")
    cloud = os.getenv("BIZ_MANAGER_MODEL_CLOUD", "claude-sonnet-4-6")
    use_cloud = os.getenv("USE_CLOUD", "false").lower() == "true"
    return claude_model(cloud) if use_cloud else ollama_model(local)
