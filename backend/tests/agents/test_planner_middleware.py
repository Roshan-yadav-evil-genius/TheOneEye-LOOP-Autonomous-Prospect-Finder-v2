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

    # Allowed write tool in plan mode
    req_add_task = MagicMock(spec=ToolCallRequest)
    req_add_task.tool_call = {"id": "2", "name": "add_task", "args": {}}
    req_add_task.config = {"configurable": {"mode": "plan"}}
    assert mw._check_permission(req_add_task) is None

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

    # Blocked in execute mode (plan creation tool)
    req_add = MagicMock(spec=ToolCallRequest)
    req_add.tool_call = {"id": "8", "name": "add_task", "args": {}}
    req_add.config = {"configurable": {"mode": "execute"}}
    res = mw._check_permission(req_add)
    assert isinstance(res, ToolMessage)
    assert res.status == "error"


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
