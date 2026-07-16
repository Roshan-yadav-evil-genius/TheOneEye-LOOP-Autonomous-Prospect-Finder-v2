from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlparse

from langchain_core.tools import BaseTool, StructuredTool


@dataclass(frozen=True)
class BrowserTaskPolicy:
    allowed_domains: frozenset[str]
    minimum_action_interval_seconds: float = 2.0
    timeout_seconds: float = 30.0


class BrowserPolicyGuard:
    """Applies domain and pacing guardrails before MCP browser actions."""

    def __init__(self, policy: BrowserTaskPolicy) -> None:
        self.policy = policy
        self._last_action_at = 0.0

    def validate_navigation(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        if not any(
            host == domain or host.endswith(f".{domain}") for domain in self.policy.allowed_domains
        ):
            raise ValueError("Navigation target is outside the task allowlist.")

    def seconds_until_next_action(self) -> float:
        elapsed = monotonic() - self._last_action_at
        return max(0.0, self.policy.minimum_action_interval_seconds - elapsed)

    def record_action(self) -> None:
        self._last_action_at = monotonic()


def compact_snapshot(snapshot: str, *, max_lines: int = 500) -> str:
    lines = snapshot.splitlines()
    compacted: list[str] = []
    previous = ""
    for line in lines:
        normalized = " ".join(line.split())
        if not normalized or normalized == previous:
            continue
        compacted.append(normalized)
        previous = normalized
        if len(compacted) >= max_lines:
            compacted.append("[snapshot truncated]")
            break
    return "\n".join(compacted)


def policy_enforced_tools(
    tools: list[BaseTool], guard: BrowserPolicyGuard
) -> list[BaseTool]:
    """Wrap MCP tools without changing their names or generated argument schemas."""
    wrapped: list[BaseTool] = []
    for inner in tools:

        async def invoke(_inner: BaseTool = inner, **arguments: object) -> object:
            url = arguments.get("url")
            if isinstance(url, str):
                guard.validate_navigation(url)
            delay = guard.seconds_until_next_action()
            if delay > 0:
                import asyncio

                await asyncio.sleep(delay)
            result = await _inner.ainvoke(arguments)
            guard.record_action()
            if isinstance(result, str) and (
                "snapshot" in _inner.name.lower() or "inspect" in _inner.name.lower()
            ):
                return compact_snapshot(result)
            return result

        wrapped.append(
            StructuredTool.from_function(
                coroutine=invoke,
                name=inner.name,
                description=inner.description,
                args_schema=inner.args_schema,
            )
        )
    return wrapped
