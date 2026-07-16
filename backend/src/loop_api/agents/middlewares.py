"""Agent middlewares shared by factory stacks (summarization when live models exist)."""

from __future__ import annotations

from typing import Any

from loop_api.core.config import get_settings


def browser_middlewares() -> list[Any]:
    """Browser-agent middlewares: optional summarization when credentials are available."""
    return _optional_summarization(keep_messages=12)


def orchestrator_middlewares() -> list[Any]:
    """Company/Contact Finder summarization when a live model is configured."""
    return _optional_summarization(keep_messages=20)


def _optional_summarization(*, keep_messages: int) -> list[Any]:
    if get_settings().model_provider == "deterministic":
        return []
    try:
        from deepagents.backends import StateBackend
        from deepagents.middleware import SummarizationMiddleware

        from loop_api.agents.model_provider import resolve_chat_model

        return [
            SummarizationMiddleware(
                model=resolve_chat_model(),
                backend=StateBackend,
                keep=("messages", keep_messages),
            )
        ]
    except Exception:
        # Middleware is best-effort; agent run must still work without credentials.
        return []
