import pytest
from unittest.mock import MagicMock
from agents.planner_middleware import PlannerModeMiddleware, extract_planner_mode
from langchain.agents.middleware import ToolCallRequest
from langchain_core.messages import ToolMessage


def test_extract_planner_mode_defaults_to_plan():
    req = MagicMock()
    req.tool_context = None
    req.config = {}
    req.runtime = None
    req.context = None
    assert extract_planner_mode(req) == "plan"


def test_extract_planner_mode_from_config():
    req = MagicMock()
    req.config = {"configurable": {"mode": "execute"}}
    assert extract_planner_mode(req) == "execute"


def test_planner_middleware_plan_mode_permissions():
    mw = PlannerModeMiddleware()

    # Allowed read tool
    req_read = MagicMock(spec=ToolCallRequest)
    req_read.tool_call = {"id": "1", "name": "get_plan_summary", "args": {}}
    req_read.config = {"configurable": {"mode": "plan"}}
    assert mw._check_permission(req_read) is None

    # Allowed write tools in plan mode
    for tool_name in ["add_task", "add_step", "update_plan_context", "update_phase", "update_task", "update_step"]:
        req_tool = MagicMock(spec=ToolCallRequest)
        req_tool.tool_call = {"id": "2", "name": tool_name, "args": {}}
        req_tool.config = {"configurable": {"mode": "plan"}}
        assert mw._check_permission(req_tool) is None, f"{tool_name} should be allowed in plan mode"

    # add_knowledge_entry is not allowed in plan mode
    req_ke = MagicMock(spec=ToolCallRequest)
    req_ke.tool_call = {"id": "2b", "name": "add_knowledge_entry", "args": {}}
    req_ke.config = {"configurable": {"mode": "plan"}}
    res_ke = mw._check_permission(req_ke)
    assert isinstance(res_ke, ToolMessage)
    assert res_ke.status == "error"

    # Blocked write tool in plan mode (base execution tool)
    req_exec = MagicMock(spec=ToolCallRequest)
    req_exec.tool_call = {"id": "3", "name": "company_register", "args": {}}
    req_exec.config = {"configurable": {"mode": "plan"}}
    res = mw._check_permission(req_exec)
    assert isinstance(res, ToolMessage)
    assert res.status == "error"
    assert res.name == "company_register"
    assert "Access Denied" in res.content


def test_planner_middleware_evaluate_mode_permissions():
    mw = PlannerModeMiddleware()

    # Allowed in evaluate mode
    req_eval = MagicMock(spec=ToolCallRequest)
    req_eval.tool_call = {"id": "4", "name": "mark_planning_as_complete", "args": {}}
    req_eval.config = {"configurable": {"mode": "evaluate"}}
    assert mw._check_permission(req_eval) is None

    # Blocked in evaluate mode (plan creation write tool)
    req_add = MagicMock(spec=ToolCallRequest)
    req_add.tool_call = {"id": "5", "name": "add_task", "args": {}}
    req_add.config = {"configurable": {"mode": "evaluate"}}
    res = mw._check_permission(req_add)
    assert isinstance(res, ToolMessage)
    assert res.status == "error"


def test_planner_middleware_execute_mode_permissions():
    mw = PlannerModeMiddleware()

    # Allowed in execute mode
    req_register = MagicMock(spec=ToolCallRequest)
    req_register.tool_call = {"id": "6", "name": "company_register", "args": {}}
    req_register.config = {"configurable": {"mode": "execute"}}
    assert mw._check_permission(req_register) is None

    # Allowed update_task_status in execute mode
    req_status = MagicMock(spec=ToolCallRequest)
    req_status.tool_call = {"id": "7", "name": "update_task_status", "args": {}}
    req_status.config = {"configurable": {"mode": "execute"}}
    assert mw._check_permission(req_status) is None

    # All tools (including plan creation tools) are allowed without restriction in execute mode
    req_add = MagicMock(spec=ToolCallRequest)
    req_add.tool_call = {"id": "8", "name": "add_task", "args": {}}
    req_add.config = {"configurable": {"mode": "execute"}}
    assert mw._check_permission(req_add) is None


def test_planner_middleware_record_mode_permissions():
    mw = PlannerModeMiddleware()

    # Allowed in record mode
    req_record = MagicMock(spec=ToolCallRequest)
    req_record.tool_call = {"id": "9", "name": "record_action_result", "args": {}}
    req_record.config = {"configurable": {"mode": "record"}}
    assert mw._check_permission(req_record) is None

    # Blocked in record mode (base execution tool)
    req_register = MagicMock(spec=ToolCallRequest)
    req_register.tool_call = {"id": "10", "name": "company_register", "args": {}}
    req_register.config = {"configurable": {"mode": "record"}}
    res = mw._check_permission(req_register)
    assert isinstance(res, ToolMessage)
    assert res.status == "error"


def test_planner_middleware_default_always_allowed_tools():
    mw = PlannerModeMiddleware()

    # Tools in DEFAULT_ALWAYS_ALLOWED_TOOLS are allowed in all modes (e.g. evaluate mode)
    req_default = MagicMock(spec=ToolCallRequest)
    req_default.tool_call = {"id": "11", "name": "Evaluation", "args": {}}
    req_default.config = {"configurable": {"mode": "evaluate"}}
    assert mw._check_permission(req_default) is None


def test_planner_middleware_subagent_type_permissions():
    mw = PlannerModeMiddleware()

    # Task tool with sales_manager is allowed in PLAN mode
    req_sm = MagicMock(spec=ToolCallRequest)
    req_sm.tool_call = {"id": "12", "name": "task", "args": {"subagent_type": "sales_manager"}}
    req_sm.config = {"configurable": {"mode": "plan"}}
    assert mw._check_permission(req_sm) is None

    # Task tool with brain_agent is allowed in PLAN mode
    req_brain = MagicMock(spec=ToolCallRequest)
    req_brain.tool_call = {"id": "13", "name": "task", "args": {"subagent_type": "brain_agent"}}
    req_brain.config = {"configurable": {"mode": "plan"}}
    assert mw._check_permission(req_brain) is None

    # Task tool with browser_agent is blocked in PLAN mode
    req_browser = MagicMock(spec=ToolCallRequest)
    req_browser.tool_call = {"id": "14", "name": "task", "args": {"subagent_type": "browser_agent"}}
    req_browser.config = {"configurable": {"mode": "plan"}}
    res = mw._check_permission(req_browser)
    assert isinstance(res, ToolMessage)
    assert res.status == "error"
    assert "Access Denied" in res.content


def test_planner_middleware_evaluation_structured_output_tool():
    mw = PlannerModeMiddleware()

    req_eval = MagicMock(spec=ToolCallRequest)
    req_eval.tool_call = {"id": "15", "name": "Evaluation", "args": {"feedback": "Good", "decision": "accept"}}
    req_eval.config = {"configurable": {"mode": "evaluate"}}
    assert mw._check_permission(req_eval) is None

    req_eval_plan = MagicMock(spec=ToolCallRequest)
    req_eval_plan.tool_call = {"id": "16", "name": "return_Evaluation", "args": {"feedback": "Good", "decision": "accept"}}
    req_eval_plan.config = {"configurable": {"mode": "plan"}}
    assert mw._check_permission(req_eval_plan) is None

