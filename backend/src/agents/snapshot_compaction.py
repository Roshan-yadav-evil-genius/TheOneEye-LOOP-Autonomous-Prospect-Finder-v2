"""Replace stale browser_snapshot ToolMessages before model calls."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, ToolMessage

BROWSER_SNAPSHOT_TOOL = "browser_snapshot"
NAVIGATION_INVALIDATING_TOOLS = frozenset(
    {
        "browser_navigate",
        "browser_navigate_back",
    }
)
EXPIRED_SNAPSHOT_PLACEHOLDER = (
    "This browser snapshot has expired and was replaced by a newer snapshot. "
    "Refer to the latest browser_snapshot result for the current page state."
)
NAVIGATION_INVALIDATED_PLACEHOLDER = (
    "This browser snapshot expired because the page changed after it was captured "
    "(navigation occurred). Call browser_snapshot to see the current page state."
)


def _is_browser_snapshot_message(message: BaseMessage) -> bool:
    return (
        isinstance(message, ToolMessage)
        and getattr(message, "name", None) == BROWSER_SNAPSHOT_TOOL
    )


def compact_stale_browser_snapshots(messages: list[BaseMessage]) -> list[ToolMessage]:
    """Return ToolMessage updates for snapshots invalidated by navigation or newer snapshots."""
    indices = [i for i, m in enumerate(messages) if _is_browser_snapshot_message(m)]
    if not indices:
        return []

    updates: list[ToolMessage] = []
    for idx in indices:
        msg = messages[idx]
        placeholder: str | None = None
        for later in messages[idx + 1 :]:
            if not isinstance(later, ToolMessage):
                continue
            name = getattr(later, "name", None)
            if name == BROWSER_SNAPSHOT_TOOL:
                placeholder = EXPIRED_SNAPSHOT_PLACEHOLDER
                break
            if name in NAVIGATION_INVALIDATING_TOOLS:
                placeholder = NAVIGATION_INVALIDATED_PLACEHOLDER
                break
        if placeholder is None:
            continue
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if content == placeholder:
            continue
        updates.append(
            ToolMessage(
                content=placeholder,
                tool_call_id=msg.tool_call_id,
                name=msg.name,
                id=msg.id,
            )
        )
    return updates


class BrowserSnapshotCompactionMiddleware:
    """Best-effort middleware shim compatible with deepagents middleware hooks."""

    def __init__(self) -> None:
        self.name = "browser_snapshot_compaction"

    def before_model(self, state: dict[str, Any], _runtime: Any = None) -> dict[str, Any] | None:
        messages = list(state.get("messages") or [])
        updates = compact_stale_browser_snapshots(messages)
        if not updates:
            return None
        by_id = {item.id: item for item in updates if item.id}
        by_call = {item.tool_call_id: item for item in updates}
        rewritten: list[BaseMessage] = []
        for message in messages:
            if isinstance(message, ToolMessage):
                replacement = None
                if message.id and message.id in by_id:
                    replacement = by_id[message.id]
                elif message.tool_call_id in by_call:
                    replacement = by_call[message.tool_call_id]
                rewritten.append(replacement or message)
            else:
                rewritten.append(message)
        return {"messages": rewritten}
