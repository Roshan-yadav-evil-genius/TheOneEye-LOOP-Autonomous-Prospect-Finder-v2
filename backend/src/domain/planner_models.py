"""
Planner Domain Models built with Pydantic v2.
Provides structured, validated, self-documenting, and serialized models
for autonomous agent workflows.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Returns timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class PlannerStatus(str, Enum):
    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Action(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the atomic action (e.g. 'act-101')"
    )
    description: str = Field(
        ...,
        description="Human-readable description of what this specific action performs"
    )
    tool: Optional[str] = Field(
        default=None,
        description="Name of the external tool or function invoked, if applicable"
    )
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of input parameters passed to the tool or action execution"
    )
    expected_output: Optional[str] = Field(
        default=None,
        description="Description or schema of the expected result produced by this action"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current execution state of the action"
    )
    result: Optional[str] = Field(
        default=None,
        description="Captured standard output, returned data, or summary of the completed action"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message, stack trace, or failure details if the action failed"
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Time taken to execute the action in milliseconds"
    )


class Step(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the step within a task (e.g. 'step-101')"
    )
    title: str = Field(
        ...,
        description="Short title describing the step objective"
    )
    description: str = Field(
        default="",
        description="Detailed summary of the operational steps to be performed"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current status of step execution"
    )
    actions: List[Action] = Field(
        default_factory=list,
        description="List of granular atomic actions executed within this step"
    )
    result: Optional[str] = Field(
        default=None,
        description="Consolidated outcome or summary of all actions completed in this step"
    )


class Task(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the task (e.g. 'task-101')"
    )
    title: str = Field(
        ...,
        description="Short, descriptive title for the task"
    )
    description: str = Field(
        default="",
        description="In-depth description of task requirements and scope"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current state of the task (PENDING, RUNNING, COMPLETED, FAILED, etc.)"
    )
    expected_output: Optional[str] = Field(
        default=None,
        description="Definition of the primary deliverable or outcome expected from this task"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of prerequisite tasks that must complete before this task can start"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool names required to execute this task"
    )
    completion_criteria: List[str] = Field(
        default_factory=list,
        description="Checklist of measurable conditions required to mark the task completed"
    )
    steps: List[Step] = Field(
        default_factory=list,
        description="Ordered sub-steps composing this task"
    )
    result: Optional[str] = Field(
        default=None,
        description="Final output summary produced upon task completion"
    )


class Phase(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the phase (e.g. 'phase-1')"
    )
    title: str = Field(
        ...,
        description="High-level title of the planning phase"
    )
    objective: str = Field(
        default="",
        description="Overarching goal and target outcome for this entire phase"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Overall completion status of the phase"
    )
    tasks: List[Task] = Field(
        default_factory=list,
        description="List of tasks grouped under this phase"
    )


class Runtime(BaseModel):
    status: PlannerStatus = Field(
        default=PlannerStatus.PLANNING,
        description="Overall execution status of the planner lifecycle (PLANNING, RUNNING, COMPLETED, etc.)"
    )
    iteration: int = Field(
        default=0,
        description="Current execution loop or agent iteration count"
    )
    checkpoint: int = Field(
        default=0,
        description="Monotonically increasing sequence number of saved state checkpoints"
    )


class Knowledge(BaseModel):
    findings: List[str] = Field(
        default_factory=list,
        description="List of key facts, observations, and discoveries learned during execution"
    )
    decisions: List[str] = Field(
        default_factory=list,
        description="List of explicit architectural or strategic choices made by the agent"
    )
    discovered_entities: List[str] = Field(
        default_factory=list,
        description="Named entities, concepts, or system components discovered during workflow"
    )


class Artifact(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the generated artifact"
    )
    name: str = Field(
        ...,
        description="Human-readable filename or title of the artifact"
    )
    path_or_uri: Optional[str] = Field(
        default=None,
        description="Absolute file path or URI pointing to the artifact storage location"
    )
    content_summary: str = Field(
        default="",
        description="Concise summary or excerpt of the artifact contents"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when the artifact was generated"
    )


class Planner(BaseModel):
    planner_id: str = Field(
        ...,
        description="Unique global identifier for this planner system instance"
    )
    version: int = Field(
        default=1,
        description="Schema version number of the planner structure"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when the planner plan was first instantiated"
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of the most recent state update or modification"
    )
    goal: str = Field(
        default="",
        description="High-level overall objective statement for the agent system"
    )
    objective: str = Field(
        default="",
        description="Detailed operational objective and scope of work"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="List of measurable conditions required for complete task success"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Operational boundaries, security guidelines, and technical limits"
    )
    phases: List[Phase] = Field(
        default_factory=list,
        description="Hierarchical list of execution phases composing the plan"
    )
    runtime: Runtime = Field(
        default_factory=Runtime,
        description="Live execution state pointers, progress tracking, and loop metrics"
    )
    knowledge: Knowledge = Field(
        default_factory=Knowledge,
        description="Agent knowledge base containing findings, decisions, and entities"
    )
    resume_note: Optional[str] = Field(
        default=None,
        description="Note or instructions left by the agent for resuming plan execution"
    )
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="Collection of files, reports, and code outputs created during execution"
    )
    final_report: Optional[str] = Field(
        default=None,
        description="Comprehensive final report generated upon workflow completion"
    )


def auto_cascade_statuses(plan: Planner) -> None:
    """
    Cascades execution statuses bottom-up from Actions -> Steps -> Tasks -> Phases -> Runtime.
    Ensures parent phases and tasks automatically reflect live progress of their child elements.
    """
    has_any_running = False

    for phase in plan.phases:
        for task in phase.tasks:
            # 1. Actions -> Step status
            for step in task.steps:
                if step.actions:
                    if all(a.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for a in step.actions):
                        step.status = TaskStatus.COMPLETED
                    elif any(a.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED) for a in step.actions):
                        if step.status == TaskStatus.PENDING:
                            step.status = TaskStatus.RUNNING
                    elif any(a.status == TaskStatus.FAILED for a in step.actions):
                        step.status = TaskStatus.FAILED

            # 2. Steps -> Task status
            if task.steps:
                if all(s.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for s in task.steps):
                    task.status = TaskStatus.COMPLETED
                elif any(s.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED) for s in task.steps):
                    if task.status == TaskStatus.PENDING:
                        task.status = TaskStatus.RUNNING
                elif any(s.status == TaskStatus.FAILED for s in task.steps):
                    task.status = TaskStatus.FAILED

            if task.status == TaskStatus.RUNNING:
                has_any_running = True

        # 3. Tasks -> Phase status
        if phase.tasks:
            if all(t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for t in phase.tasks):
                phase.status = TaskStatus.COMPLETED
            elif any(t.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED) for t in phase.tasks):
                if phase.status == TaskStatus.PENDING:
                    phase.status = TaskStatus.RUNNING
            elif any(t.status == TaskStatus.FAILED for t in phase.tasks):
                phase.status = TaskStatus.FAILED

        if phase.status == TaskStatus.RUNNING:
            has_any_running = True

    if has_any_running and plan.runtime.status == PlannerStatus.PLANNING:
        plan.runtime.status = PlannerStatus.RUNNING


def validate_dependencies(
    plan: Planner,
    target_phase_id: str,
    target_task_id: str,
    target_step_id: Optional[str] = None,
) -> Optional[str]:
    """
    Validates sequential phase, task, and step execution order.
    Returns an error message string if dependencies are unsatisfied, or None if execution order is valid.
    """
    # 1. Phase Sequence Check
    target_phase_idx = -1
    for idx, phase in enumerate(plan.phases):
        if phase.id == target_phase_id:
            target_phase_idx = idx
            break

    if target_phase_idx > 0:
        for prev_phase in plan.phases[:target_phase_idx]:
            if prev_phase.status not in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
                return (
                    f"Dependency Error: Cannot execute Phase '{plan.phases[target_phase_idx].title}' ({target_phase_id}). "
                    f"Preceding Phase '{prev_phase.title}' ({prev_phase.id}) is currently {prev_phase.status.value}. "
                    f"Please complete Phase '{prev_phase.title}' before starting Phase '{target_phase_id}'."
                )

    # 2. Task Sequence & Declared Dependency Check
    target_phase = plan.phases[target_phase_idx] if target_phase_idx >= 0 else None
    if target_phase:
        target_task_idx = -1
        for idx, task in enumerate(target_phase.tasks):
            if task.id == target_task_id:
                target_task_idx = idx
                break

        if target_task_idx >= 0:
            target_task = target_phase.tasks[target_task_idx]

            # Check declared task dependencies first
            if target_task.dependencies:
                all_tasks = {t.id: t for p in plan.phases for t in p.tasks}
                for dep_id in target_task.dependencies:
                    dep_task = all_tasks.get(dep_id)
                    if not dep_task or dep_task.status not in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
                        dep_status = dep_task.status.value if dep_task else "not found"
                        return (
                            f"Dependency Error: Cannot execute Task '{target_task.title}' ({target_task.id}). "
                            f"Prerequisite Task '{dep_id}' is not completed (current status: {dep_status})."
                        )
            # Default sequential task ordering within phase if no dependencies declared
            elif target_task_idx > 0:
                for prev_task in target_phase.tasks[:target_task_idx]:
                    if prev_task.status not in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
                        return (
                            f"Dependency Error: Cannot execute Task '{target_task.title}' ({target_task.id}). "
                            f"Preceding Task '{prev_task.title}' ({prev_task.id}) is currently {prev_task.status.value}. "
                            f"Please complete Task '{prev_task.title}' first."
                        )

            # 3. Step Sequence Check within task
            if target_step_id and target_task.steps:
                target_step_idx = -1
                for idx, step in enumerate(target_task.steps):
                    if step.id == target_step_id:
                        target_step_idx = idx
                        break

                if target_step_idx > 0:
                    for prev_step in target_task.steps[:target_step_idx]:
                        if prev_step.status not in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
                            return (
                                f"Dependency Error: Cannot execute Step '{target_task.steps[target_step_idx].title}' ({target_step_id}). "
                                f"Preceding Step '{prev_step.title}' ({prev_step.id}) is currently {prev_step.status.value}. "
                                f"Please complete Step '{prev_step.title}' first."
                            )

    return None

