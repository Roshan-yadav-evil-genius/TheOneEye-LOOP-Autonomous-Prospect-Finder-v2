"""
Planner Agent 8-Tool Suite implementation for autonomous research & orchestration.
"""

from typing import Any, Dict, List, Literal, Optional
from langchain_core.tools import BaseTool, tool
from sqlalchemy.ext.asyncio import AsyncSession

from application.planner_service import PlannerService
from domain.planner_models import (
    Action,
    ActionType,
    Artifact,
    Phase,
    Planner,
    PlannerStatus,
    Step,
    Task,
    TaskStatus,
)


def company_planner_tools(
    session: AsyncSession,
    strategy_id: Optional[str],
    effort_prefix: str,
) -> List[BaseTool]:
    """Factory returning the 8-tool Planner suite bound to an AsyncSession and effort_prefix."""
    planner_service = PlannerService(session)

    async def _get_plan() -> Planner:
        return await planner_service.get_or_create_plan(
            effort_prefix=effort_prefix,
            strategy_id=strategy_id,
        )

    @tool
    async def get_plan_summary() -> Dict[str, Any]:
        """Get structured overview of the current execution plan, phases, runtime progress, knowledge, and artifacts."""
        plan = await _get_plan()
        return plan.model_dump(mode="json")

    @tool
    async def update_plan_context(
        goal: Optional[str] = None,
        objective: Optional[str] = None,
        success_criteria: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update top-level strategic goal, operational objective, success criteria checklist, or operational constraints of the plan."""
        plan = await _get_plan()
        if goal is not None:
            plan.goal = goal
        if objective is not None:
            plan.objective = objective
        if success_criteria is not None:
            plan.success_criteria = success_criteria
        if constraints is not None:
            plan.constraints = constraints

        updated_plan = await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {
            "status": "success",
            "goal": updated_plan.goal,
            "objective": updated_plan.objective,
            "success_criteria": updated_plan.success_criteria,
            "constraints": updated_plan.constraints,
        }

    @tool
    async def add_task(
        phase_id: str,
        title: str,
        description: str = "",
        dependencies: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        completion_criteria: Optional[List[str]] = None,
        expected_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a new task to an existing phase in the planner roadmap."""
        plan = await _get_plan()
        phase = next((p for p in plan.phases if p.id == phase_id), None)
        if not phase:
            phase = Phase(
                id=phase_id,
                title=f"Phase {phase_id}",
                objective="Generated Phase",
                tasks=[],
            )
            plan.phases.append(phase)

        task_num = len(phase.tasks) + 1
        new_task = Task(
            id=f"{phase_id}-task-{task_num}",
            title=title,
            description=description,
            dependencies=dependencies or [],
            tools=tools or [],
            completion_criteria=completion_criteria or [],
            expected_output=expected_output,
            status=TaskStatus.PENDING,
        )
        phase.tasks.append(new_task)
        updated_plan = await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {
            "status": "success",
            "task_id": new_task.id,
            "progress": updated_plan.runtime.progress,
        }

    @tool
    async def add_step(
        task_id: str,
        title: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Add a granular operational step to a task."""
        plan = await _get_plan()
        target_task = None
        for phase in plan.phases:
            for task in phase.tasks:
                if task.id == task_id:
                    target_task = task
                    break

        if not target_task:
            return {"status": "error", "message": f"Task '{task_id}' not found."}

        step_num = len(target_task.steps) + 1
        new_step = Step(
            id=f"{task_id}-step-{step_num}",
            title=title,
            description=description,
            status=TaskStatus.PENDING,
        )
        target_task.steps.append(new_step)
        await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {"status": "success", "step_id": new_step.id}

    @tool
    async def update_task_status(
        task_id: str,
        status: str,
        result: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the status (e.g. 'running', 'completed', 'failed', 'blocked') and output result of a task."""
        plan = await _get_plan()
        target_task = None
        for phase in plan.phases:
            for task in phase.tasks:
                if task.id == task_id:
                    target_task = task
                    break

        if not target_task:
            return {"status": "error", "message": f"Task '{task_id}' not found."}

        try:
            enum_status = TaskStatus(status.lower())
        except ValueError:
            enum_status = TaskStatus.RUNNING

        target_task.status = enum_status
        if result is not None:
            target_task.result = result

        plan.runtime.current_task = task_id
        if enum_status == TaskStatus.RUNNING:
            plan.runtime.status = PlannerStatus.RUNNING

        updated_plan = await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {
            "status": "success",
            "task_id": task_id,
            "task_status": enum_status.value,
            "overall_progress": updated_plan.runtime.progress,
        }

    @tool
    async def record_action_result(
        task_id: str,
        step_id: str,
        description: str,
        tool: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record the outcome of a tool execution, reasoning step, or subagent action within a task step."""
        plan = await _get_plan()
        target_step = None
        for phase in plan.phases:
            for task in phase.tasks:
                if task.id == task_id:
                    for step in task.steps:
                        if step.id == step_id:
                            target_step = step
                            break

        if not target_step:
            return {
                "status": "error",
                "message": f"Step '{step_id}' in Task '{task_id}' not found.",
            }

        action_id = f"{step_id}-act-{len(target_step.actions) + 1}"
        action_status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
        new_action = Action(
            id=action_id,
            type=ActionType.TOOL_CALL if tool else ActionType.REASONING,
            description=description,
            tool=tool,
            inputs=inputs or {},
            status=action_status,
            result=result,
            error=error,
        )
        target_step.actions.append(new_action)
        if result:
            target_step.result = result
            target_step.status = TaskStatus.COMPLETED

        await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {"status": "success", "action_id": action_id}

    @tool
    async def add_knowledge_entry(
        category: Literal["findings", "decisions", "discovered_entities"],
        detail: str,
    ) -> Dict[str, Any]:
        """Record strategic observations, architectural decisions, or discovered entities into the plan knowledge base."""
        plan = await _get_plan()
        if category == "findings":
            plan.knowledge.findings.append(detail)
        elif category == "decisions":
            plan.knowledge.decisions.append(detail)
        elif category == "discovered_entities":
            plan.knowledge.discovered_entities.append(detail)
        else:
            return {"status": "error", "message": f"Invalid category '{category}'."}

        await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {
            "status": "success",
            "category": category,
            "count": len(getattr(plan.knowledge, category)),
        }

    @tool
    async def register_artifact(
        name: str,
        type: str,
        path_or_uri: Optional[str] = None,
        content_summary: str = "",
    ) -> Dict[str, Any]:
        """Register a report, source file, JSON data dump, or output document produced during effort execution."""
        plan = await _get_plan()
        artifact_id = f"artifact-{len(plan.artifacts) + 1}"
        art = Artifact(
            id=artifact_id,
            name=name,
            type=type,
            path_or_uri=path_or_uri,
            content_summary=content_summary,
        )
        plan.artifacts.append(art)
        await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {"status": "success", "artifact_id": artifact_id, "name": name}

    @tool
    async def finalize_plan(
        final_report: str,
    ) -> Dict[str, Any]:
        """Finalize the plan, set runtime status to COMPLETED, and record the final summary report."""
        plan = await _get_plan()
        plan.runtime.status = PlannerStatus.COMPLETED
        plan.final_report = final_report
        for phase in plan.phases:
            if phase.status != TaskStatus.FAILED:
                phase.status = TaskStatus.COMPLETED
            for task in phase.tasks:
                if task.status != TaskStatus.FAILED:
                    task.status = TaskStatus.COMPLETED

        updated_plan = await planner_service.save_plan(
            effort_prefix, plan, strategy_id=strategy_id
        )
        return {
            "status": "success",
            "runtime_status": updated_plan.runtime.status.value,
            "final_progress": updated_plan.runtime.progress,
        }

    return [
        get_plan_summary,
        update_plan_context,
        add_task,
        add_step,
        update_task_status,
        record_action_result,
        add_knowledge_entry,
        register_artifact,
        finalize_plan,
    ]
