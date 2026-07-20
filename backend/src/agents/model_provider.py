import json
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.config import Settings, get_settings
from observability.logging import get_logger

log = get_logger("loop.model_provider")


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


def _harness_profile_key(provider: str, model_name: str) -> str:
    """Build a deepagents profile key that never exceeds one ':'."""
    # Ollama tags like qwen3.5:4b already contain ':'; do not prepend provider.
    if ":" in model_name:
        return model_name
    return f"{provider}:{model_name}"


def resolve_chat_model(settings: Settings | None = None) -> BaseChatModel:
    config = settings or get_settings()
    model: BaseChatModel
    if config.model_provider == "openai":
        if not config.model_api_key:
            raise RuntimeError("LOOP_MODEL_API_KEY is required for the OpenAI provider.")
        log.info("resolve_chat_model", provider="openai", model=config.model_name)
        model = ChatOpenAI(
            model=config.model_name,
            api_key=SecretStr(config.model_api_key),
            base_url=config.model_base_url or None,
            model_kwargs={"parallel_tool_calls": False},
        )
    elif config.model_provider == "ollama":
        base_url = config.model_base_url or "http://127.0.0.1:11434"
        log.info(
            "resolve_chat_model",
            provider="ollama",
            model=config.model_name,
            base_url=base_url,
        )
        model = ChatOllama(
            model=config.model_name,
            base_url=base_url,
        )
    else:
        raise RuntimeError("The deterministic provider has no live BaseChatModel.")

    # Exclude the default deepagents SummarizationMiddleware so we can use our own custom keep config
    import dataclasses
    from deepagents import register_harness_profile
    from deepagents.profiles.harness.harness_profiles import _harness_profile_for_model

    base_profile = _harness_profile_for_model(model, None)
    new_profile = dataclasses.replace(
        base_profile,
        excluded_middleware=base_profile.excluded_middleware | {"SummarizationMiddleware"},
    )
    key = _harness_profile_key(config.model_provider, config.model_name)
    register_harness_profile(key, new_profile)
    register_harness_profile(config.model_provider, new_profile)

    return model


def resolve_discovery_model(settings: Settings | None = None) -> DiscoveryModel:
    config = settings or get_settings()
    if config.model_provider == "deterministic":
        log.info("resolve_discovery_model", provider="deterministic")
        return DeterministicDiscoveryModel()
    log.info("resolve_discovery_model", provider=config.model_provider, model=config.model_name)
    return LangChainDiscoveryModel(resolve_chat_model(config))
