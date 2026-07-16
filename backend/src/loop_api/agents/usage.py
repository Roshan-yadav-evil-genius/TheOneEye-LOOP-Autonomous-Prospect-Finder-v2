"""Attribute model/token/cost fields onto AgentRun (local-safe helpers)."""

from __future__ import annotations

from typing import Any

from loop_api.persistence import models


def apply_usage(run: models.AgentRun, usage: dict[str, Any] | None) -> None:
    """Copy provider usage metadata when present; deterministic runs record zeros."""
    payload = usage or {}
    run.prompt_tokens = int(payload.get("prompt_tokens") or payload.get("input_tokens") or 0)
    run.completion_tokens = int(
        payload.get("completion_tokens") or payload.get("output_tokens") or 0
    )
    run.estimated_cost = float(payload.get("estimated_cost") or 0.0)
