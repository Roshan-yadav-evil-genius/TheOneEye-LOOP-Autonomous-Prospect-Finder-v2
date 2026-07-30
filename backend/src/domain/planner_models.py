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


class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    REASONING = "reasoning"
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    HTTP_REQUEST = "http_request"
    HUMAN_INPUT = "human_input"
    CHECKPOINT = "checkpoint"
    UPDATE_KNOWLEDGE = "update_knowledge"


class Action(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the atomic action (e.g. 'act-101')"
    )
    type: ActionType = Field(
        default=ActionType.TOOL_CALL,
        description="Categorical type of the action (tool call, search, reasoning, code execution, etc.)"
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
    current_phase: Optional[str] = Field(
        default=None,
        description="ID of the phase currently active during execution"
    )
    current_task: Optional[str] = Field(
        default=None,
        description="ID of the task currently being executed by the agent"
    )
    current_step: Optional[str] = Field(
        default=None,
        description="ID of the active step being processed"
    )
    next_action: Optional[Action] = Field(
        default=None,
        description="Next structured Action object queued for execution by the agent runner"
    )
    progress: float = Field(
        default=0.0,
        description="Overall completion progress expressed as a percentage from 0.0 to 100.0"
    )
    iteration: int = Field(
        default=0,
        description="Current execution loop or agent iteration count"
    )
    checkpoint: int = Field(
        default=0,
        description="Monotonically increasing sequence number of saved state checkpoints"
    )


class Resume(BaseModel):
    resume_phase: Optional[str] = Field(
        default=None,
        description="Phase ID where execution should resume after recovery or restart"
    )
    resume_task: Optional[str] = Field(
        default=None,
        description="Task ID to target when resuming context"
    )
    resume_step: Optional[str] = Field(
        default=None,
        description="Step ID to start execution from upon resumption"
    )
    first_action: Optional[str] = Field(
        default=None,
        description="ID of the first action to execute when resuming work"
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
    type: str = Field(
        ...,
        description="MIME type or custom category (e.g. 'python_source', 'markdown_report', 'json_data')"
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
        ...,
        description="High-level overall objective statement for the agent system"
    )
    objective: str = Field(
        ...,
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
    resume: Resume = Field(
        default_factory=Resume,
        description="State recovery pointers for resuming execution after interrupts or context resets"
    )
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="Collection of files, reports, and code outputs created during execution"
    )
    final_report: Optional[str] = Field(
        default=None,
        description="Comprehensive final report generated upon workflow completion"
    )
