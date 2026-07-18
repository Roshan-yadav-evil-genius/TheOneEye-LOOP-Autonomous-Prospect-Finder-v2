"""Nested checkpoint helpers for CompiledSubAgent resume semantics.

Implements RecreationDocs AgentWithBrowser/03-checkpoints-and-threads.md:
reuse active child thread ids, GPA allocation only for new work, and
checkpoint-aware invoke (task vs None) with drain-until-idle.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, Literal

from deepagents import CompiledSubAgent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

from agents.runtime import build_role_thread_id

AllocationMode = Literal["role", "gpa", "named"]


@dataclass
class ActiveChildThread:
    thread_id: str
    status: Literal["running", "completed"]
    allocation_mode: AllocationMode
    task_fingerprint: str | None = None


def build_named_child_thread_id(parent_thread_id: str, child_suffix: str) -> str:
    return f"{parent_thread_id}:{child_suffix}"


def resolve_compiled_child_thread_id(
    *,
    parent_state: dict[str, Any],
    invocation_key: str,
    allocation_mode: AllocationMode,
    effort_prefix: str,
    role_suffix: str | None = None,
    parent_role_thread: str | None = None,
    existing_thread_ids: list[str] | None = None,
    child_suffix: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Reuse an active child thread or allocate a new one into parent state."""
    active = dict(parent_state.get("active_subagent_threads") or {})
    current = active.get(invocation_key)
    if current and current.get("status") == "running" and current.get("thread_id"):
        return str(current["thread_id"]), parent_state

    if allocation_mode == "gpa":
        if not parent_role_thread:
            raise ValueError("parent_role_thread is required for GPA allocation")
        from agents.runtime import allocate_gpa_thread_id, collect_gpa_thread_ids

        # Never allocate a new GPA while any GPA entry is still running.
        for item in active.values():
            thread_id_candidate = str(item.get("thread_id") or "")
            if (
                item.get("status") == "running"
                and thread_id_candidate.startswith(f"{parent_role_thread}_GPA_")
            ):
                return thread_id_candidate, parent_state
        known = collect_gpa_thread_ids(parent_role_thread, active) + list(
            existing_thread_ids or []
        )
        thread_id = allocate_gpa_thread_id(parent_role_thread, known)
    elif allocation_mode == "role":
        if not role_suffix:
            raise ValueError("role_suffix is required for role allocation")
        thread_id = build_role_thread_id(effort_prefix=effort_prefix, role_suffix=role_suffix)
    else:
        if not parent_role_thread or not child_suffix:
            raise ValueError("named allocation requires parent_role_thread and child_suffix")
        thread_id = build_named_child_thread_id(parent_role_thread, child_suffix)

    active[invocation_key] = asdict(
        ActiveChildThread(
            thread_id=thread_id,
            status="running",
            allocation_mode=allocation_mode,
        )
    )
    return thread_id, {**parent_state, "active_subagent_threads": active}


def mark_child_completed(parent_state: dict[str, Any], invocation_key: str) -> dict[str, Any]:
    active = dict(parent_state.get("active_subagent_threads") or {})
    entry = dict(active.get(invocation_key) or {})
    if entry:
        entry["status"] = "completed"
        active[invocation_key] = entry
    return {**parent_state, "active_subagent_threads": active}


async def resolve_subagent_input(
    agent_graph: Any,
    agent_config: dict[str, Any],
    task: Any,
) -> Any:
    """Return task for a fresh/completed turn, or None to resume pending nodes."""
    if not hasattr(agent_graph, "aget_state"):
        return task
    snapshot = await agent_graph.aget_state(agent_config)
    if getattr(snapshot, "next", ()):
        return None
    values = getattr(snapshot, "values", {}) or {}
    messages: list[BaseMessage] = list(values.get("messages") or [])
    if not messages:
        return task
    last = messages[-1]
    if not isinstance(last, AIMessage):
        return None
    if isinstance(task, dict) and "messages" in task:
        task_messages = task["messages"]
        if task_messages:
            content = (
                task_messages[-1].content
                if isinstance(task_messages[-1], HumanMessage)
                else task_messages[-1].get("content")
                if isinstance(task_messages[-1], dict)
                else None
            )
            for message in messages:
                if isinstance(message, HumanMessage) and message.content == content:
                    return None
    return task


async def invoke_compiled_child_until_idle(
    child: Any,
    *,
    thread_id: str,
    task: Any,
) -> Any:
    config = {"configurable": {"thread_id": thread_id}}
    invoke_input = await resolve_subagent_input(child, config, task)
    result = await child.ainvoke(invoke_input, config)
    while True:
        if not hasattr(child, "aget_state"):
            return result
        snapshot = await child.aget_state(config)
        if not getattr(snapshot, "next", ()):
            return result
        result = await child.ainvoke(None, config)


def to_checkpointed_compiled_subagent(
    *,
    name: str,
    description: str,
    child_graph: Any,
    effort_prefix: str,
    allocation_mode: AllocationMode,
    role_suffix: str | None = None,
    parent_role_thread: str | None = None,
    list_existing_thread_ids: Callable[[str], list[str]],
    load_parent_state: Callable[[str], dict[str, Any]] | None = None,
    save_parent_state: Callable[[str, dict[str, Any]], None] | None = None,
) -> Any:
    """Wrap a compiled child so parents persist and reuse nested thread ids."""

    async def runnable(task: Any, config: dict[str, Any] | None = None) -> Any:
        parent_thread = (config or {}).get("configurable", {}).get("thread_id") or (
            parent_role_thread or ""
        )
        parent_state: dict[str, Any] = {"active_subagent_threads": {}}
        if load_parent_state and parent_thread:
            parent_state = load_parent_state(parent_thread) or parent_state
        existing = list_existing_thread_ids(parent_thread)
        child_thread, next_state = resolve_compiled_child_thread_id(
            parent_state=parent_state,
            invocation_key=name,
            allocation_mode=allocation_mode,
            effort_prefix=effort_prefix,
            role_suffix=role_suffix,
            parent_role_thread=parent_role_thread or parent_thread,
            existing_thread_ids=existing,
        )
        if save_parent_state and parent_thread:
            save_parent_state(parent_thread, next_state)
        result = await invoke_compiled_child_until_idle(
            child_graph, thread_id=child_thread, task=task
        )
        completed = mark_child_completed(next_state, name)
        if save_parent_state and parent_thread:
            save_parent_state(parent_thread, completed)
        return result

    return CompiledSubAgent(
        name=name,
        description=description,
        runnable=RunnableLambda(runnable),
    )
