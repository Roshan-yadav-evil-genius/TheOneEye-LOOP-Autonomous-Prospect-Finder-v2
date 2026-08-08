"""
Planner Agent 8-Tool Suite implementation for autonomous research & orchestration.
Standardized with explicit LangChain args_schema Pydantic validation models.
Concurrency-safe with isolated session scopes and async serialization lock.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Literal, Optional
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from application.planner_service import PlannerService
from domain.planner_models import (
    Action,
    Artifact,
    Phase,
    Planner,
    PlannerStatus,
    Step,
    Task,
    TaskStatus,
    auto_cascade_statuses,
    validate_dependencies,
)
from persistence.database import SessionFactory


@asynccontextmanager
async def _get_db_session(provided_session: Optional[AsyncSession]) -> AsyncIterator[AsyncSession]:
    if provided_session is not None:
        yield provided_session
    else:
        async with SessionFactory() as db_session:
            yield db_session


def _coerce_to_list(v: Any) -> List[str]:
    """Pre-validation helper to coerce None, single strings, or iterables into List[str]."""
    if v is None:
        return []
    if isinstance(v, str):
        v_str = v.strip()
        return [v_str] if v_str else []
    if isinstance(v, (list, tuple, set)):
        res = []
        for item in v:
            if item is not None:
                item_str = str(item).strip()
                if item_str:
                    res.append(item_str)
        return res
    return [str(v)]


# ============================================================================
# Explicit Pydantic Input Schemas for Planner Tools
# ============================================================================


class UpdatePlanContextInput(BaseModel):
    goal: Optional[str] = Field(
        default=None,
        description="High-level strategic goal statement for the effort plan. Example: 'Identify qualified B2B prospects'",
    )
    objective: Optional[str] = Field(
        default=None,
        description="Detailed operational objective and scope of work. Example: 'Discover and verify top 50 ICP tech leads'",
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="List of verifiable success criteria strings. Example: ['10 qualified prospects registered', 'All emails verified']",
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="List of operational constraints or guardrails. Example: ['GDPR compliance required', 'Exclude agency models']",
    )

    @field_validator("success_criteria", "constraints", mode="before")
    @classmethod
    def coerce_list_fields(cls, v: Any) -> List[str]:
        return _coerce_to_list(v)


class AddTaskInput(BaseModel):
    phase_id: str = Field(
        ...,
        description="Target phase ID to append this task to. Example: 'phase-1'",
    )
    title: str = Field(
        ...,
        description="Short, actionable title for the task. Example: 'Analyze Target Market'",
    )
    description: str = Field(
        default="",
        description="In-depth summary of task requirements and execution scope.",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prerequisite task IDs that must complete before this task can start. Example: ['phase-1-task-1']",
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool names required to execute this task. Example: ['web_search', 'register_company']",
    )
    completion_criteria: List[str] = Field(
        default_factory=list,
        description="List of verifiable completion criteria strings. Example: ['ICP matched', 'Data verified']",
    )
    expected_output: Optional[str] = Field(
        default=None,
        description="Definition of expected primary deliverable or outcome from this task.",
    )

    @field_validator("dependencies", "tools", "completion_criteria", mode="before")
    @classmethod
    def coerce_list_fields(cls, v: Any) -> List[str]:
        return _coerce_to_list(v)


class AddStepInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Target task ID to add this step to. Example: 'phase-1-task-1'",
    )
    title: str = Field(
        ...,
        description="Short title describing the step objective. Example: 'Query Brain Memory'",
    )
    description: str = Field(
        default="",
        description="Detailed summary of operational actions to perform in this step.",
    )


class UpdateTaskStatusInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Task ID to update status for. Example: 'phase-1-task-1'",
    )
    status: str = Field(
        ...,
        description="New execution status string. Allowed values: 'pending', 'ready', 'running', 'blocked', 'completed', 'failed', 'skipped'. Example: 'running'",
    )
    result: Optional[str] = Field(
        default=None,
        description="Captured standard output, final deliverable summary, or output result of the task.",
    )


class RecordActionResultInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Task ID containing the step. Example: 'phase-1-task-1'",
    )
    step_id: str = Field(
        ...,
        description="Step ID where action was performed. Example: 'phase-1-task-1-step-1'",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the specific action taken or tool invoked.",
    )
    tool: Optional[str] = Field(
        default=None,
        description="Name of the external tool or function invoked, if applicable. Example: 'recall_memory'",
    )
    inputs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of input parameters passed to the tool or action execution.",
    )
    result: Optional[str] = Field(
        default=None,
        description="Captured output, returned data, or summary of the completed action.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message or failure details if the action failed.",
    )


class AddKnowledgeEntryInput(BaseModel):
    category: Literal["findings", "decisions", "discovered_entities"] = Field(
        ...,
        description="Category of knowledge base entry: 'findings' (observations), 'decisions' (choices), or 'discovered_entities' (entities found).",
    )
    detail: str = Field(
        ...,
        description="Detailed text content or summary of the strategic observation, decision, or discovered entity.",
    )


class RegisterArtifactInput(BaseModel):
    name: str = Field(
        ...,
        description="Human-readable filename or title of the artifact. Example: 'ICP Market Report.pdf'",
    )
    path_or_uri: Optional[str] = Field(
        default=None,
        description="Absolute file path or URI pointing to the artifact storage location.",
    )
    content_summary: str = Field(
        default="",
        description="Concise summary or excerpt describing the contents of the artifact.",
    )


class FinalizePlanInput(BaseModel):
    final_report: str = Field(
        ...,
        description="Comprehensive final summary report summarizing all findings, completed roadmap, and execution results.",
    )


# ============================================================================
# Planner Tools Factory & Granular Tool Groups
# ============================================================================


def get_plan_creation_tools(
    session: Optional[AsyncSession],
    strategy_id: Optional[str],
    effort_prefix: str,
) -> List[BaseTool]:
    """Return tools for plan creation and context setup (Planner Agent)."""
    db_lock = asyncio.Lock()

    @tool
    async def get_plan_summary() -> Dict[str, Any]:
        """Get structured overview of the current execution plan, phases, runtime progress, knowledge, and artifacts."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                return plan.model_dump(mode="json")

    @tool(args_schema=UpdatePlanContextInput)
    async def update_plan_context(
        goal: Optional[str] = None,
        objective: Optional[str] = None,
        success_criteria: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
    ) -> str:
        """Update top-level strategic goal, operational objective, success criteria checklist, or operational constraints of the plan."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                if goal is not None:
                    plan.goal = goal
                if objective is not None:
                    plan.objective = objective
                if success_criteria:
                    plan.success_criteria = success_criteria
                if constraints:
                    plan.constraints = constraints

                await planner_service.save_plan(
                    effort_prefix, plan, strategy_id=strategy_id
                )
                return "Updated"

    @tool(args_schema=AddTaskInput)
    async def add_task(
        phase_id: str,
        title: str,
        description: str = "",
        dependencies: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        completion_criteria: Optional[List[str]] = None,
        expected_output: Optional[str] = None,
    ) -> str:
        """Add a new task to an existing phase in the planner roadmap."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
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
                await planner_service.save_plan(
                    effort_prefix, plan, strategy_id=strategy_id
                )
                return f"Task added: {new_task.id}"

    @tool(args_schema=AddStepInput)
    async def add_step(
        task_id: str,
        title: str,
        description: str = "",
    ) -> str:
        """Add a granular operational step to a task."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                target_task = None
                for phase in plan.phases:
                    for task in phase.tasks:
                        if task.id == task_id:
                            target_task = task
                            break

                if not target_task:
                    return f"Error: Task '{task_id}' not found."

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
                return f"Step added: {new_step.id}"

    @tool(args_schema=AddKnowledgeEntryInput)
    async def add_knowledge_entry(
        category: Literal["findings", "decisions", "discovered_entities"],
        detail: str,
    ) -> str:
        """Record strategic observations, architectural decisions, or discovered entities into the plan knowledge base."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                if category == "findings":
                    plan.knowledge.findings.append(detail)
                elif category == "decisions":
                    plan.knowledge.decisions.append(detail)
                elif category == "discovered_entities":
                    plan.knowledge.discovered_entities.append(detail)
                else:
                    return f"Error: Invalid category '{category}'."

                await planner_service.save_plan(
                    effort_prefix, plan, strategy_id=strategy_id
                )
                return "Saved"

    return [
        get_plan_summary,
        update_plan_context,
        add_task,
        add_step,
        add_knowledge_entry,
    ]


def get_plan_evaluator_tools(
    session: Optional[AsyncSession],
    strategy_id: Optional[str],
    effort_prefix: str,
) -> List[BaseTool]:
    """Return tools for plan evaluation and approval (Evaluator Agent)."""
    db_lock = asyncio.Lock()

    @tool
    async def get_plan_summary() -> Dict[str, Any]:
        """Get structured overview of the current execution plan, phases, runtime progress, knowledge, and artifacts."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                return plan.model_dump(mode="json")

    @tool
    async def mark_planning_as_complete() -> str:
        """Mark the planning phase as complete and set the plan runtime status to READY for execution workers."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                plan.runtime.status = PlannerStatus.READY
                await planner_service.save_plan(
                    effort_prefix, plan, strategy_id=strategy_id
                )
                return "Plan status set to ready."

    return [
        mark_planning_as_complete,
        get_plan_summary,
    ]


def get_plan_status_updater_tools(
    session: Optional[AsyncSession],
    strategy_id: Optional[str],
    effort_prefix: str,
) -> List[BaseTool]:
    """Return tools for updating task status (Execution Workers)."""
    db_lock = asyncio.Lock()

    @tool(args_schema=UpdateTaskStatusInput)
    async def update_task_status(
        task_id: str,
        status: str,
        result: Optional[str] = None,
    ) -> str:
        """Update the status (e.g. 'running', 'completed', 'failed', 'blocked') and output result of a task."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                target_phase = None
                target_task = None
                for phase in plan.phases:
                    for task in phase.tasks:
                        if task.id == task_id:
                            target_phase = phase
                            target_task = task
                            break

                if not target_task or not target_phase:
                    return f"Error: Task '{task_id}' not found."

                try:
                    enum_status = TaskStatus(status.lower())
                except ValueError:
                    enum_status = TaskStatus.RUNNING

                if enum_status in (TaskStatus.RUNNING, TaskStatus.COMPLETED):
                    dep_error = validate_dependencies(
                        plan=plan,
                        target_phase_id=target_phase.id,
                        target_task_id=target_task.id,
                    )
                    if dep_error:
                        return dep_error

                target_task.status = enum_status
                if result is not None:
                    target_task.result = result

                if enum_status == TaskStatus.RUNNING:
                    plan.runtime.status = PlannerStatus.RUNNING

                await planner_service.save_plan(
                    effort_prefix, plan, strategy_id=strategy_id
                )
                return "Updated"

    return [
        update_task_status,
    ]


def get_plan_monitoring_tools(
    session: Optional[AsyncSession],
    strategy_id: Optional[str],
    effort_prefix: str,
) -> List[BaseTool]:
    """Return tools for progress monitoring and plan finalization."""
    db_lock = asyncio.Lock()

    @tool(args_schema=RecordActionResultInput)
    async def record_action_result(
        task_id: str,
        step_id: str,
        description: str,
        tool: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> str:
        """Record the outcome of a tool execution, reasoning step, or subagent action within a task step."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                target_phase = None
                target_task = None
                target_step = None
                for phase in plan.phases:
                    for task in phase.tasks:
                        if task.id == task_id:
                            for step in task.steps:
                                if step.id == step_id:
                                    target_phase = phase
                                    target_task = task
                                    target_step = step
                                    break

                if not target_step or not target_task or not target_phase:
                    return f"Error: Step '{step_id}' in Task '{task_id}' not found."

                dep_error = validate_dependencies(
                    plan=plan,
                    target_phase_id=target_phase.id,
                    target_task_id=target_task.id,
                    target_step_id=target_step.id,
                )
                if dep_error:
                    return dep_error

                action_id = f"{step_id}-act-{len(target_step.actions) + 1}"
                action_status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
                new_action = Action(
                    id=action_id,
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
                return f"Saved: {action_id}"

    @tool(args_schema=FinalizePlanInput)
    async def finalize_plan(
        final_report: str,
    ) -> str:
        """Finalize the plan, set runtime status to COMPLETED, and record the final summary report."""
        async with db_lock:
            async with _get_db_session(session) as db_session:
                planner_service = PlannerService(db_session)
                plan = await planner_service.get_or_create_plan(
                    effort_prefix=effort_prefix,
                    strategy_id=strategy_id,
                )
                plan.runtime.status = PlannerStatus.COMPLETED
                plan.final_report = final_report
                for phase in plan.phases:
                    if phase.status != TaskStatus.FAILED:
                        phase.status = TaskStatus.COMPLETED
                    for task in phase.tasks:
                        if task.status != TaskStatus.FAILED:
                            task.status = TaskStatus.COMPLETED

                await planner_service.save_plan(
                    effort_prefix, plan, strategy_id=strategy_id
                )
                return "Finalized"

    return [
        record_action_result,
        finalize_plan,
    ]
