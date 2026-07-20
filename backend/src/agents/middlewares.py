"""Agent middlewares shared by factory stacks (summarization when live models exist)."""

from __future__ import annotations

from typing import Any

from agents.snapshot_compaction import BrowserSnapshotCompactionMiddleware
from core.config import get_settings


def browser_middlewares() -> list[Any]:
    """Browser-agent middlewares: snapshot compaction + optional summarization."""
    middlewares: list[Any] = [BrowserSnapshotCompactionMiddleware()]
    middlewares.extend(_optional_summarization(keep_messages=12))
    return middlewares


def orchestrator_middlewares() -> list[Any]:
    """Company/Contact Finder summarization when a live model is configured."""
    return _optional_summarization(keep_messages=20)


def _optional_summarization(*, keep_messages: int) -> list[Any]:
    if get_settings().model_provider == "deterministic":
        return []
    try:
        from deepagents.middleware import SummarizationMiddleware

        from agents.filesystem_backend import default_filesystem_backend
        from agents.model_provider import resolve_chat_model

        return [
            SummarizationMiddleware(
                model=resolve_chat_model(),
                backend=default_filesystem_backend(),
                keep=("messages", keep_messages),
            )
        ]
    except Exception:
        # Middleware is best-effort; agent run must still work without credentials.
        return []
