"""Nested checkpoint acceptance matrix from AgentWithBrowser/03-checkpoints-and-threads.md."""

from types import SimpleNamespace
from typing import Any

import pytest

from loop_api.agents.nested_checkpointing import (
    invoke_compiled_child_until_idle,
    mark_child_completed,
    resolve_compiled_child_thread_id,
    resolve_subagent_input,
    to_checkpointed_compiled_subagent,
)
from loop_api.agents.runtime import allocate_gpa_thread_id


def test_fresh_gpa_allocates_gpa_1() -> None:
    thread, state = resolve_compiled_child_thread_id(
        parent_state={},
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[],
    )
    assert thread == "LOOP_p_s_1_company_finder_GPA_1"
    assert state["active_subagent_threads"]["General Purpose Agent"]["status"] == "running"


def test_second_completed_gpa_allocates_gpa_2() -> None:
    first, state = resolve_compiled_child_thread_id(
        parent_state={},
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[],
    )
    state = mark_child_completed(state, "General Purpose Agent")
    second, state = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[first],
    )
    assert second == "LOOP_p_s_1_company_finder_GPA_2"


def test_interrupted_gpa_is_reused_on_resume() -> None:
    interrupted, state = resolve_compiled_child_thread_id(
        parent_state={},
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[
            "LOOP_p_s_1_company_finder_GPA_1",
            "LOOP_p_s_1_company_finder_GPA_2",
        ],
    )
    assert interrupted.endswith("_GPA_3")
    reused, _ = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[interrupted],
    )
    assert reused == interrupted


def test_multiple_compiled_children_have_separate_ids() -> None:
    browser, state = resolve_compiled_child_thread_id(
        parent_state={},
        invocation_key="browser_agent",
        allocation_mode="role",
        effort_prefix="LOOP_p_s_1",
        role_suffix="browser_agent",
    )
    brain, state = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="company_finder_brain",
        allocation_mode="role",
        effort_prefix="LOOP_p_s_1",
        role_suffix="company_finder_brain",
    )
    gpa, state = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[],
    )
    assert len({browser, brain, gpa}) == 3


@pytest.mark.asyncio
async def test_pending_tool_call_invokes_with_none() -> None:
    class Child:
        def __init__(self) -> None:
            self.calls: list[Any] = []
            self._pending = True

        async def aget_state(self, _config: dict[str, Any]) -> SimpleNamespace:
            return SimpleNamespace(
                next=("tools",) if self._pending else (),
                values={"messages": []},
            )

        async def ainvoke(self, payload: Any, _config: dict[str, Any]) -> str:
            self.calls.append(payload)
            self._pending = False
            return "ok"

    child = Child()
    result = await invoke_compiled_child_until_idle(
        child, thread_id="t1", task={"messages": [{"role": "user", "content": "go"}]}
    )
    assert result == "ok"
    assert child.calls[0] is None


@pytest.mark.asyncio
async def test_resolve_subagent_input_fresh_returns_task() -> None:
    class Child:
        async def aget_state(self, _config: dict[str, Any]) -> SimpleNamespace:
            return SimpleNamespace(next=(), values={"messages": []})

    task = {"messages": [{"role": "user", "content": "x"}]}
    assert await resolve_subagent_input(Child(), {"configurable": {"thread_id": "t"}}, task) is task


def test_allocate_gpa_is_monotonic() -> None:
    assert allocate_gpa_thread_id("parent", []) == "parent_GPA_1"
    assert allocate_gpa_thread_id("parent", ["parent_GPA_1", "parent_GPA_3"]) == "parent_GPA_4"


@pytest.mark.asyncio
async def test_compiled_subagent_wrapper_marks_completion() -> None:
    registry: dict[str, dict[str, Any]] = {}

    class Child:
        async def aget_state(self, _config: dict[str, Any]) -> SimpleNamespace:
            return SimpleNamespace(next=(), values={"messages": []})

        async def ainvoke(self, _payload: Any, _config: dict[str, Any]) -> str:
            return "done"

    wrapper = to_checkpointed_compiled_subagent(
        name="browser_agent",
        description="browser",
        child_graph=Child(),
        effort_prefix="LOOP_p_s_1",
        allocation_mode="role",
        role_suffix="browser_agent",
        parent_role_thread="LOOP_p_s_1_company_finder",
        list_existing_thread_ids=lambda _: [],
        load_parent_state=lambda key: registry.get(key, {"active_subagent_threads": {}}),
        save_parent_state=lambda key, state: registry.__setitem__(key, state),
    )
    result = await wrapper["runnable"].ainvoke(
        {"messages": []}, {"configurable": {"thread_id": "LOOP_p_s_1_company_finder"}}
    )
    assert result == "done"
    entry = registry["LOOP_p_s_1_company_finder"]["active_subagent_threads"]["browser_agent"]
    assert entry["status"] == "completed"
