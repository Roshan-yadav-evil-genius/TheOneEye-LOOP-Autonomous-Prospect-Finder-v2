import json
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.config import Settings, get_settings


class DiscoveryModel(Protocol):
    async def decide(self, prompt: str) -> dict[str, Any]: ...


class DeterministicDiscoveryModel:
    """Credential-free model used only by tests and explicitly configured local runs."""

    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.responses = list(responses or [])

    async def decide(self, prompt: str) -> dict[str, Any]:
        del prompt
        if not self.responses:
            return {"action": "no_candidate", "reason": "deterministic response queue is empty"}
        return self.responses.pop(0)


class LangChainDiscoveryModel:
    def __init__(self, model: BaseChatModel) -> None:
        self.model = model

    async def decide(self, prompt: str) -> dict[str, Any]:
        response = await self.model.ainvoke(prompt)
        content = response.content
        text = content if isinstance(content, str) else json.dumps(content)
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Model must return a JSON discovery decision.") from exc
        if not isinstance(value, dict):
            raise ValueError("Model discovery decision must be an object.")
        return value


def resolve_chat_model(settings: Settings | None = None) -> BaseChatModel:
    config = settings or get_settings()
    if config.model_provider == "openai":
        if not config.model_api_key:
            raise RuntimeError("LOOP_MODEL_API_KEY is required for the OpenAI provider.")
        return ChatOpenAI(
            model=config.model_name,
            api_key=SecretStr(config.model_api_key),
            base_url=config.model_base_url or None,
            model_kwargs={"parallel_tool_calls": False},
        )
    if config.model_provider == "ollama":
        return ChatOllama(
            model=config.model_name,
            base_url=config.model_base_url or "http://127.0.0.1:11434",
        )
    raise RuntimeError("The deterministic provider has no live BaseChatModel.")


def resolve_discovery_model(settings: Settings | None = None) -> DiscoveryModel:
    config = settings or get_settings()
    if config.model_provider == "deterministic":
        return DeterministicDiscoveryModel()
    return LangChainDiscoveryModel(resolve_chat_model(config))
