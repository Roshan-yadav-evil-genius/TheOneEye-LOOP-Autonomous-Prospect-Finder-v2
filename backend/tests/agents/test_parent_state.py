import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agents.parent_state import ParentSubagentStateStore
from agents.nested_checkpointing import resolve_compiled_child_thread_id


@pytest.mark.asyncio
async def test_parent_state_survives_flush_roundtrip(session: AsyncSession) -> None:
    store = ParentSubagentStateStore(session)
    parent = "LOOP_o_p_s_1_company_finder"
    store.bind(parent, {"active_subagent_threads": {}})
    _, state = resolve_compiled_child_thread_id(
        parent_state=store.sync_load(parent),
        invocation_key="browser_agent",
        allocation_mode="role",
        effort_prefix="LOOP_o_p_s_1",
        role_suffix="browser_agent",
        parent_role_thread=parent,
    )
    store.sync_save(parent, state)
    await store.flush()

    reloaded = await store.load(parent)
    assert "browser_agent" in reloaded["active_subagent_threads"]
    assert (
        reloaded["active_subagent_threads"]["browser_agent"]["thread_id"]
        == "LOOP_o_p_s_1_browser_agent"
    )
