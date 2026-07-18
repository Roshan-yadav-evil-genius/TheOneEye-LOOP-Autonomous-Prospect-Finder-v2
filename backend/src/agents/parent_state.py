"""Durable parent nested-subagent state for GPA/role resume across restarts."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence import models


class ParentSubagentStateStore:
    """Persist ``active_subagent_threads`` keyed by parent role thread id."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._cache: dict[str, dict[str, Any]] = {}
        self._dirty: set[str] = set()

    async def load(self, parent_thread_id: str) -> dict[str, Any]:
        row = await self.session.scalar(
            select(models.AgentSubagentState).where(
                models.AgentSubagentState.parent_thread_id == parent_thread_id
            )
        )
        if not row:
            return {"active_subagent_threads": {}}
        return {"active_subagent_threads": dict(row.active_subagent_threads or {})}

    async def save(self, parent_thread_id: str, state: dict[str, Any]) -> None:
        row = await self.session.scalar(
            select(models.AgentSubagentState).where(
                models.AgentSubagentState.parent_thread_id == parent_thread_id
            )
        )
        payload = dict(state.get("active_subagent_threads") or {})
        if not row:
            row = models.AgentSubagentState(parent_thread_id=parent_thread_id)
            self.session.add(row)
        row.active_subagent_threads = payload
        await self.session.commit()

    def sync_load(self, parent_thread_id: str) -> dict[str, Any]:
        return dict(self._cache.get(parent_thread_id) or {"active_subagent_threads": {}})

    def sync_save(self, parent_thread_id: str, state: dict[str, Any]) -> None:
        self._cache[parent_thread_id] = {
            "active_subagent_threads": dict(state.get("active_subagent_threads") or {})
        }
        self._dirty.add(parent_thread_id)

    def bind(self, parent_thread_id: str, initial: dict[str, Any] | None = None) -> None:
        self._cache[parent_thread_id] = dict(initial or {"active_subagent_threads": {}})

    async def flush(self) -> None:
        for parent_thread_id in list(self._dirty):
            await self.save(parent_thread_id, self._cache.get(parent_thread_id, {}))
        self._dirty.clear()


def make_parent_state_callbacks(
    store: ParentSubagentStateStore, parent_thread_id: str
) -> tuple[Any, Any, Any]:
    """Return (list_existing, load_state, save_state) for nested checkpointing."""
    store.bind(parent_thread_id)

    def list_existing(parent_thread: str) -> list[str]:
        state = store.sync_load(parent_thread)
        active = state.get("active_subagent_threads") or {}
        return [str(item["thread_id"]) for item in active.values() if item.get("thread_id")]

    def load_state(parent_thread: str) -> dict[str, Any]:
        return store.sync_load(parent_thread)

    def save_state(parent_thread: str, state: dict[str, Any]) -> None:
        store.sync_save(parent_thread, state)

    return list_existing, load_state, save_state
