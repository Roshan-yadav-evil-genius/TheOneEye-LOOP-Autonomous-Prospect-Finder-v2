"""Structured SubAgent Middleware for deepagents.

Forces parent agents to map delegation requests into a strict, structured
Pydantic payload (StructuredTask), ensuring sub-agents receive actionable,
contextualized, and zero-memory self-contained task prompts.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Sequence
from typing import Annotated, Any, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.subagents import (
    _EXCLUDED_STATE_KEYS,
    CompiledSubAgent,
    SubAgent,
    SubAgentMiddleware,
    _subagent_tracing_context,
    create_sub_agent,
)
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import InjectedToolCallId, StructuredTool
from langgraph.types import Command


class StructuredTask(BaseModel):
    """A structured, self-contained task description for a sub-agent."""

    model_config = ConfigDict(extra="ignore")

    objective: str = Field(
        ...,
        description=(
            "The precise, primary goal the sub-agent must accomplish. Start with"
            " an action verb."
        ),
    )
    context: str = Field(
        default="",
        description=(
            "All necessary background information, raw data, or previous steps."
            " Assume the sub-agent has zero prior memory—include everything it"
            " needs to know here."
        ),
    )
    expected_output: str = Field(
        default="Clear, comprehensive, and structured response.",
        description=(
            "The exact format and structure of the desired output (e.g., 'A"
            " JSON object with keys X and Y', 'A markdown table', 'A"
            " 2-paragraph summary')."
        ),
    )
    constraints: list[str] = Field(
        default_factory=list,
        description=(
            "A list of strict rules, limitations, or things to explicitly avoid"
            " while executing the task."
        ),
    )

    @field_validator("objective", "context", "expected_output", mode="before")
    @classmethod
    def coerce_str_fields(cls, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (list, tuple)):
            return "\n".join(str(item) for item in v)
        if isinstance(v, dict):
            return json.dumps(v)
        return str(v)

    @field_validator("constraints", mode="before")
    @classmethod
    def coerce_constraints(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, (list, tuple)):
            return [str(item) for item in v]
        return [str(v)]


class DelegateToSubAgent(BaseModel):
    """Tool schema for delegating tasks to specialized sub-agents."""

    model_config = ConfigDict(extra="ignore")

    subagent_type: str = Field(
        ...,
        description=(
            "The specific type of sub-agent to route this task to (e.g.,"
            " 'brain_agent', 'sales_manager', 'browser_agent')."
        ),
    )
    task: StructuredTask = Field(
        ...,
        description="The structured, self-contained task payload.",
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(
        default="",
        description="Injected ToolCall ID from LangGraph / LangChain.",
    )

    @model_validator(mode="before")
    @classmethod
    def prepare_task_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "task" not in data:
            task_dict: dict[str, Any] = {}
            if "objective" in data:
                task_dict["objective"] = data["objective"]
            elif "description" in data:
                task_dict["objective"] = data["description"]

            if "context" in data:
                task_dict["context"] = data["context"]
            if "expected_output" in data:
                task_dict["expected_output"] = data["expected_output"]
            if "constraints" in data:
                task_dict["constraints"] = data["constraints"]

            if "objective" in task_dict:
                data["task"] = task_dict
        return data


def format_structured_prompt(task: StructuredTask) -> str:
    """Formats StructuredTask Pydantic model into a deterministic markdown prompt."""
    constraints_str = (
        "\n".join(f"- {c}" for c in task.constraints)
        if task.constraints
        else "None"
    )

    return f"""### SUB-AGENT TASK EXECUTION SPECIFICATION

#### OBJECTIVE
{task.objective}

#### CONTEXT & BACKGROUND
{task.context or 'None provided.'}

#### EXPECTED OUTPUT FORMAT
{task.expected_output}

#### CONSTRAINTS & GUARDRAILS
{constraints_str}
"""


STRUCTURED_TASK_TOOL_DESCRIPTION = """Launch an ephemeral subagent to handle a complex, multi-step task in an isolated context window.

Available agent types and the tools they have access to:
{available_agents}

Specify subagent_type to select the agent and pass a structured task object with objective, context, expected_output, and constraints.
Usage notes:
- Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls.
- Each invocation is stateless: the agent sees only the prompt you give it and returns a single final report. Embed all context in the structured task payload.
- The agent's report is not shown to the user; relay a summary yourself.
- Tell the agent whether to create content, analyze, or only research, since it cannot see the user's intent."""


def _compile_spec(
    spec: SubAgent | CompiledSubAgent,
    *,
    state_schema: type | None = None,
) -> CompiledSubAgent:
    """Compile one raw spec or configure one provided runnable."""
    if "runnable" in spec:
        compiled = cast("CompiledSubAgent", spec)
        runnable = compiled["runnable"].with_config(
            {
                "metadata": {"lc_agent_name": spec["name"]},
                "run_name": spec["name"],
            }
        )
        return {
            "name": spec["name"],
            "description": spec["description"],
            "runnable": runnable,
        }
    return {
        "name": spec["name"],
        "description": spec["description"],
        "runnable": create_sub_agent(
            spec,
            state_schema=state_schema,
        ),
    }


def build_structured_task_tool(
    subagents: Sequence[SubAgent | CompiledSubAgent],
    task_description: str | None = None,
    *,
    private_state_keys: frozenset[str] = frozenset(),
    state_schema: type | None = None,
) -> BaseTool:
    """Create a task tool using DelegateToSubAgent schema from subagent specs."""
    compiled_subagents = [
        _compile_spec(spec, state_schema=state_schema) for spec in subagents
    ]
    subagent_graphs: dict[str, Runnable] = {
        spec["name"]: spec["runnable"] for spec in compiled_subagents
    }

    subagent_description_str = "\n".join(
        f"- {s['name']}: {s['description']}" for s in compiled_subagents
    )

    if task_description is None:
        description = STRUCTURED_TASK_TOOL_DESCRIPTION.format(
            available_agents=subagent_description_str
        )
    elif "{available_agents}" in task_description:
        description = task_description.format(
            available_agents=subagent_description_str
        )
    else:
        description = task_description

    def _return_command_with_state_update(result: dict, tool_call_id: str) -> Command:
        if "messages" not in result:
            error_msg = (
                "CompiledSubAgent must return a state containing a 'messages' key."
            )
            raise ValueError(error_msg)

        state_update = {}
        for k, v in result.items():
            if k in _EXCLUDED_STATE_KEYS or k in private_state_keys:
                continue
            if isinstance(v, BaseMessage):
                continue
            if isinstance(v, list) and v and isinstance(v[0], BaseMessage):
                continue
            state_update[k] = v

        structured = result.get("structured_response")
        if structured is not None:
            if hasattr(structured, "model_dump_json"):
                content: str = structured.model_dump_json()
            elif dataclasses.is_dataclass(structured) and not isinstance(
                structured, type
            ):
                content = json.dumps(dataclasses.asdict(structured))
            else:
                content = json.dumps(structured)
        else:
            content = ""
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    text = msg.text.rstrip() if msg.text else ""
                    if text:
                        content = text
                        break

        return Command(
            update={
                **state_update,
                "messages": [ToolMessage(content, tool_call_id=tool_call_id)],
            }
        )

    def _validate_and_prepare_state(
        subagent_type: str,
        task_payload: StructuredTask,
    ) -> tuple[Runnable, dict]:
        subagent = subagent_graphs[subagent_type]
        prompt = format_structured_prompt(task_payload)
        subagent_state = {"messages": [HumanMessage(content=prompt)]}
        return subagent, subagent_state

    def task(
        subagent_type: str,
        task: StructuredTask,
        tool_call_id: Annotated[str, InjectedToolCallId] = "",
    ) -> str | Command:
        effective_tool_call_id = tool_call_id or "subagent_task"
        if subagent_type not in subagent_graphs:
            allowed_types = ", ".join([f"`{k}`" for k in subagent_graphs])
            return (
                f"We cannot invoke subagent {subagent_type} because it does not"
                f" exist, the only allowed types are {allowed_types}"
            )
        subagent, subagent_state = _validate_and_prepare_state(
            subagent_type,
            task,
        )
        subagent_config: RunnableConfig = {
            "configurable": {"ls_agent_type": "subagent"}
        }
        with _subagent_tracing_context():
            result = subagent.invoke(subagent_state, subagent_config)
        return _return_command_with_state_update(result, effective_tool_call_id)

    async def atask(
        subagent_type: str,
        task: StructuredTask,
        tool_call_id: Annotated[str, InjectedToolCallId] = "",
    ) -> str | Command:
        effective_tool_call_id = tool_call_id or "subagent_task"
        if subagent_type not in subagent_graphs:
            allowed_types = ", ".join([f"`{k}`" for k in subagent_graphs])
            return (
                f"We cannot invoke subagent {subagent_type} because it does not"
                f" exist, the only allowed types are {allowed_types}"
            )
        subagent, subagent_state = _validate_and_prepare_state(
            subagent_type,
            task,
        )
        subagent_config: RunnableConfig = {
            "configurable": {"ls_agent_type": "subagent"}
        }
        with _subagent_tracing_context():
            result = await subagent.ainvoke(subagent_state, subagent_config)
        return _return_command_with_state_update(result, effective_tool_call_id)

    return StructuredTool.from_function(
        name="task",
        func=task,
        coroutine=atask,
        description=description,
        args_schema=DelegateToSubAgent,
    )


class StructuredSubAgentMiddleware(SubAgentMiddleware):
    """Middleware providing subagents with structured task schema via a `task` tool."""

    def __init__(
        self,
        *,
        backend: BackendProtocol,
        subagents: Sequence[SubAgent | CompiledSubAgent],
        system_prompt: str | None = None,
        task_description: str | None = None,
        private_state_keys: frozenset[str] | None = None,
        state_schema: type | None = None,
    ) -> None:
        super().__init__(
            backend=backend,
            subagents=subagents,
            system_prompt=system_prompt,
            task_description=task_description,
            private_state_keys=private_state_keys,
            state_schema=state_schema,
        )

        self.subagent_names = frozenset(spec["name"] for spec in subagents)

        task_tool = build_structured_task_tool(
            self._subagents,
            task_description,
            private_state_keys=self._private_state_keys,
            state_schema=self._state_schema,
        )

        # Build system prompt with available agents
        if system_prompt and subagents:
            agents_desc = "\n".join(
                f"- {s['name']}: {s['description']}" for s in subagents
            )
            self.system_prompt = (
                system_prompt
                + "\n\nAvailable subagent types:\n\n"
                + agents_desc
            )
        else:
            self.system_prompt = system_prompt

        self.tools = [task_tool]

    @property
    def private_state_keys(self) -> frozenset[str]:
        return self._private_state_keys

    @private_state_keys.setter
    def private_state_keys(self, value: frozenset[str]) -> None:
        self._private_state_keys = value
        task_tool = build_structured_task_tool(
            self._subagents,
            task_description=self._task_description,
            private_state_keys=value,
            state_schema=self._state_schema,
        )
        self.tools = [task_tool]
