"""Redact secrets and session material from logs, checkpoints, and tool payloads."""

from __future__ import annotations

import re
from typing import Any

_SECRET_PATTERNS = (
    re.compile(
        r"(?i)(authorization|cookie|set-cookie|x-li-auth|csrf|token)\s*[:=]\s*.+"
    ),
    re.compile(r"(?i)bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"li_at=[^;\s]+"),
    re.compile(r"JSESSIONID=[^;\s]+"),
)

_REDACTED = "[REDACTED]"


def redact_text(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_REDACTED, redacted)
    return redacted


def redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if any(
                token in lowered
                for token in ("cookie", "token", "authorization", "password", "secret", "session")
            ):
                out[key] = _REDACTED
            else:
                out[key] = redact_payload(item)
        return out
    return value
