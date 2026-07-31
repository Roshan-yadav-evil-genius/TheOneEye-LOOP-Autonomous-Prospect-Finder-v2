import pytest
from domain.planner_models import TaskStatus, PlannerStatus
from agents.planner_tools import company_planner_tools
from application.planner_service import PlannerService


@pytest.mark.asyncio
async def test_planner_tool_suite_execution(session):
    strategy_id = "strat-123"
    effort_prefix = "LOOP_org1_prod1_strat123_1"

    tools_list = company_planner_tools(session, strategy_id, effort_prefix)
    tool_map = {t.name: t for t in tools_list}

    # Verify all 9 tools exist
    expected_tools = {
        "get_plan_summary",
        "update_plan_context",
        "add_task",
        "add_step",
        "update_task_status",
        "record_action_result",
        "add_knowledge_entry",
        "register_artifact",
        "finalize_plan",
    }
    assert expected_tools.issubset(set(tool_map.keys()))

    # 1. Tool 1: get_plan_summary
    summary = await tool_map["get_plan_summary"].ainvoke({})
    assert summary["planner_id"] == f"planner-{effort_prefix}"
    assert len(summary["phases"]) == 0
    phase_id = "phase-1"

    # 1b. Tool: update_plan_context
    context_res = await tool_map["update_plan_context"].ainvoke({
        "success_criteria": ["Find at least 10 qualified companies", "Verify contact email"],
        "constraints": ["EU GDPR compliance required", "Exclude agency model companies"],
    })
    assert context_res["status"] == "success"
    assert len(context_res["success_criteria"]) == 2
    assert len(context_res["constraints"]) == 2

    # 2. Tool 2: add_task
    task_res = await tool_map["add_task"].ainvoke({
        "phase_id": phase_id,
        "title": "Analyze Target Market",
        "description": "Identify top 10 ICP tech companies",
    })
    assert task_res["status"] == "success"
    task_id = task_res["task_id"]

    # 3. Tool 3: add_step
    step_res = await tool_map["add_step"].ainvoke({
        "task_id": task_id,
        "title": "Query Brain Memory",
        "description": "Recall past strategies",
    })
    assert step_res["status"] == "success"
    step_id = step_res["step_id"]

    # 4. Tool 4: update_task_status (RUNNING)
    status_res1 = await tool_map["update_task_status"].ainvoke({
        "task_id": task_id,
        "status": "running",
    })
    assert status_res1["status"] == "success"
    assert status_res1["task_status"] == "running"

    # 5. Tool 5: record_action_result
    act_res = await tool_map["record_action_result"].ainvoke({
        "task_id": task_id,
        "step_id": step_id,
        "description": "Executed brain recall query",
        "tool": "recall_memory",
        "result": "Found 3 relevant strategies",
    })
    assert act_res["status"] == "success"

    # 6. Tool 6: add_knowledge_entry
    know_res = await tool_map["add_knowledge_entry"].ainvoke({
        "category": "findings",
        "detail": "Target market is shifting toward AI-native SaaS companies.",
    })
    assert know_res["status"] == "success"
    assert know_res["count"] == 1

    # 7. Tool 7: register_artifact
    art_res = await tool_map["register_artifact"].ainvoke({
        "name": "ICP Market Report.pdf",
        "content_summary": "Comprehensive analysis of top targets",
    })
    assert art_res["status"] == "success"

    # 8. Tool 4: update_task_status (COMPLETED)
    status_res2 = await tool_map["update_task_status"].ainvoke({
        "task_id": task_id,
        "status": "completed",
        "result": "Found 10 qualified targets",
    })
    assert status_res2["status"] == "success"

    # 9. Tool 8: finalize_plan
    final_res = await tool_map["finalize_plan"].ainvoke({
        "final_report": "Planning phase complete. All targets verified.",
    })
    assert final_res["status"] == "success"
    assert final_res["runtime_status"] == PlannerStatus.COMPLETED.value

    # Verify directly via PlannerService
    service = PlannerService(session)
    final_plan = await service.get_plan(effort_prefix)
    assert final_plan is not None
    assert final_plan.runtime.status == PlannerStatus.COMPLETED
    assert len(final_plan.knowledge.findings) == 1
    assert final_plan.knowledge.findings[0] == "Target market is shifting toward AI-native SaaS companies."
    assert len(final_plan.artifacts) == 1
    assert final_plan.artifacts[0].name == "ICP Market Report.pdf"
    assert final_plan.final_report == "Planning phase complete. All targets verified."


@pytest.mark.asyncio
async def test_wrap_tool_for_planner_permission_denied():
    from langchain_core.tools import tool
    from agents.tools import wrap_tool_for_planner

    @tool
    def allowed_tool() -> str:
        """Allowed planner tool."""
        return "ok"
    allowed_tool.name = "add_task"

    @tool
    def execution_tool(name: str) -> str:
        """Execution tool forbidden for planner."""
        return f"registered {name}"
    execution_tool.name = "register_company"

    # Test allowed tool returns unmodified
    wrapped_allowed = wrap_tool_for_planner(allowed_tool)
    assert wrapped_allowed is allowed_tool
    assert wrapped_allowed.invoke({}) == "ok"

    # Test planning mode execution tool returns Planning mode error message
    wrapped_planning = wrap_tool_for_planner(execution_tool, mode="planning")
    assert wrapped_planning is not execution_tool
    res_planning = await wrapped_planning.ainvoke({"name": "Acme Corp"})
    assert "Permission Denied: Tool 'register_company' is an execution tool" in res_planning
    assert "cannot be called during Planning mode" in res_planning
    assert "[PLANNING MODE - FORBIDDEN TOOL]" in wrapped_planning.description

    # Test progress tools (update_task_status) forbidden in planning mode
    @tool
    def status_tool(task_id: str, status: str) -> str:
        """Update task status tool."""
        return f"status {status}"
    status_tool.name = "update_task_status"

    wrapped_status_planning = wrap_tool_for_planner(status_tool, mode="planning")
    assert wrapped_status_planning is not status_tool
    res_status_planning = await wrapped_status_planning.ainvoke({"task_id": "t1", "status": "running"})
    assert "Permission Denied: Tool 'update_task_status' tracks execution progress/results" in res_status_planning
    assert "cannot be called during Planning mode" in res_status_planning

    # Test progress tools allowed in analyzing mode
    wrapped_status_analyzing = wrap_tool_for_planner(status_tool, mode="analyzing")
    assert wrapped_status_analyzing is status_tool

    # Test analyzing mode execution tool returns Analyzing mode error message
    wrapped_analyzing = wrap_tool_for_planner(execution_tool, mode="analyzing")
    assert wrapped_analyzing is not execution_tool
    res_analyzing = await wrapped_analyzing.ainvoke({"name": "Acme Corp"})
    assert "Permission Denied: Tool 'register_company' is an execution tool" in res_analyzing
    assert "cannot be called during Analyzing mode" in res_analyzing
    assert "You are only allowed to inspect results, record insights" in res_analyzing
    assert "[ANALYZING MODE - FORBIDDEN TOOL]" in wrapped_analyzing.description



