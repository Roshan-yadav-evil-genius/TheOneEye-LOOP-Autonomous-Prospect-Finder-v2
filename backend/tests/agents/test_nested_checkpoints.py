from agents.nested_checkpointing import (
    mark_child_completed,
    resolve_compiled_child_thread_id,
)
from agents.runtime import assemble_system_prompt


def test_assemble_system_prompt_self_improving_base() -> None:
    prompt = assemble_system_prompt(name="Company Finder", responsibility="Find companies.")
    assert prompt.startswith("You are Company Finder.")
    assert "Find companies." in prompt


def test_fresh_gpa_allocates_one() -> None:
    thread_id, state = resolve_compiled_child_thread_id(
        parent_state={"active_subagent_threads": {}},
        invocation_key="gpa_task",
        allocation_mode="gpa",
        effort_prefix="LOOP_o_p_s_1",
        parent_role_thread="LOOP_o_p_s_1_company_finder",
        existing_thread_ids=[],
    )
    assert thread_id == "LOOP_o_p_s_1_company_finder_GPA_1"
    assert state["active_subagent_threads"]["gpa_task"]["status"] == "running"


def test_second_gpa_after_completion() -> None:
    state = {
        "active_subagent_threads": {
            "gpa_task": {
                "thread_id": "LOOP_o_p_s_1_company_finder_GPA_1",
                "status": "completed",
                "allocation_mode": "gpa",
            }
        }
    }
    thread_id, next_state = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="gpa_task",
        allocation_mode="gpa",
        effort_prefix="LOOP_o_p_s_1",
        parent_role_thread="LOOP_o_p_s_1_company_finder",
        existing_thread_ids=["LOOP_o_p_s_1_company_finder_GPA_1"],
    )
    assert thread_id == "LOOP_o_p_s_1_company_finder_GPA_2"
    assert next_state["active_subagent_threads"]["gpa_task"]["thread_id"] == thread_id


def test_interrupted_gpa_resumes_same_id() -> None:
    state = {
        "active_subagent_threads": {
            "gpa_task": {
                "thread_id": "LOOP_o_p_s_1_company_finder_GPA_3",
                "status": "running",
                "allocation_mode": "gpa",
            }
        }
    }
    thread_id, next_state = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="gpa_task",
        allocation_mode="gpa",
        effort_prefix="LOOP_o_p_s_1",
        parent_role_thread="LOOP_o_p_s_1_company_finder",
        existing_thread_ids=["LOOP_o_p_s_1_company_finder_GPA_3"],
    )
    assert thread_id == "LOOP_o_p_s_1_company_finder_GPA_3"
    assert next_state is state


def test_running_gpa_blocks_new_allocation() -> None:
    state = {
        "active_subagent_threads": {
            "other": {
                "thread_id": "LOOP_o_p_s_1_company_finder_GPA_2",
                "status": "running",
                "allocation_mode": "gpa",
            }
        }
    }
    thread_id, _ = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="gpa_task",
        allocation_mode="gpa",
        effort_prefix="LOOP_o_p_s_1",
        parent_role_thread="LOOP_o_p_s_1_company_finder",
        existing_thread_ids=[],
    )
    assert thread_id == "LOOP_o_p_s_1_company_finder_GPA_2"


def test_role_children_are_stable() -> None:
    thread_id, state = resolve_compiled_child_thread_id(
        parent_state={"active_subagent_threads": {}},
        invocation_key="browser_agent",
        allocation_mode="role",
        effort_prefix="LOOP_o_p_s_1",
        role_suffix="browser_agent",
        parent_role_thread="LOOP_o_p_s_1_company_finder",
    )
    assert thread_id == "LOOP_o_p_s_1_browser_agent"
    completed = mark_child_completed(state, "browser_agent")
    assert completed["active_subagent_threads"]["browser_agent"]["status"] == "completed"
