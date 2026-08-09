"""Planner & Layered Mode Middleware for dynamic permission enforcement across agent modes."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable
import structlog
from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class PlannerMode(str, Enum):
    """Operational mode string enum for Planner agent permissions."""

    PLAN = "plan"
    EVALUATE = "evaluate"
    EXECUTE = "execute"
    RECORD = "record"


class AgentContext(BaseModel):
    """Runtime context passed during agent execution (e.g., context=AgentContext(mode=PlannerMode.PLAN))."""

    mode: PlannerMode = PlannerMode.PLAN


def extract_planner_mode(request: Any) -> PlannerMode:
    """Extract operational planner mode (PLAN, EVALUATE, EXECUTE, RECORD) from request context/runtime."""
    def _val(val: Any) -> PlannerMode | None:
        if isinstance(val, PlannerMode):
            return val
        if isinstance(val, str) and val.strip():
            try:
                return PlannerMode(val.strip().lower())
            except ValueError:
                return None
        return None

    # 1. Runtime context on request (e.g., request.runtime.context.mode)
    runtime = getattr(request, "runtime", None)
    if runtime is not None and hasattr(runtime, "context"):
        ctx = getattr(runtime, "context", None)
        if ctx is not None:
            m = _val(getattr(ctx, "mode", None)) or (ctx.get("mode") if isinstance(ctx, dict) else None)
            parsed = _val(m)
            if parsed:
                return parsed

    # 2. Direct context on request (e.g., request.context.mode)
    ctx = getattr(request, "context", None)
    if ctx is not None:
        m = _val(getattr(ctx, "mode", None)) or (ctx.get("mode") if isinstance(ctx, dict) else None)
        parsed = _val(m)
        if parsed:
            return parsed

    # 3. Direct tool_context on request
    tc = getattr(request, "tool_context", None)
    if tc is not None and not isinstance(tc, type(MagicMock if "MagicMock" in globals() else object)):
        m = _val(getattr(tc, "mode", None)) or (tc.get("mode") if isinstance(tc, dict) else None)
        parsed = _val(m)
        if parsed:
            return parsed

    # 4. Config dictionary on request
    config = getattr(request, "config", None)
    if isinstance(config, dict):
        configurable = config.get("configurable", {})
        if isinstance(configurable, dict):
            tc = configurable.get("tool_context")
            if tc is not None:
                m = _val(getattr(tc, "mode", None)) or (tc.get("mode") if isinstance(tc, dict) else None)
                parsed = _val(m)
                if parsed:
                    return parsed
            parsed = _val(configurable.get("mode"))
            if parsed:
                return parsed

    # 5. Direct request dictionary
    if isinstance(request, dict):
        parsed = _val(request.get("mode"))
        if parsed:
            return parsed

    return PlannerMode.PLAN


class PlannerModeMiddleware(AgentMiddleware):
    """Enforces mode-specific read-only write permissions across 4 modes: PLAN, EVALUATE, EXECUTE, RECORD."""

    # Set of default direct tool names universally allowed across all modes without restriction
    DEFAULT_ALWAYS_ALLOWED_TOOLS: set[str] = {
        "get_plan_summary",
        "Evaluation",
        "return_Evaluation",
    }

    # Set of subagent types universally allowed during planning/evaluation phases
    ALWAYS_ALLOWED_SUBAGENTS: set[str] = {
        "sales_manager",
        "brain_agent",
    }

    # Explicit whitelist of write tools permitted per mode.
    ALLOWED_WRITES: dict[PlannerMode, set[str]] = {
        PlannerMode.PLAN: {
            "add_task",
            "add_step",
            "update_plan_context",
            "add_knowledge_entry",
        },
        PlannerMode.EVALUATE: {
            "mark_planning_as_complete",
        },
        PlannerMode.RECORD: {
            "record_action_result",
            "update_task_status",
            "mark_plan_as_finished",
        },
    }

    def is_tool_allowed(self, tool_name: str, mode: PlannerMode) -> bool:
        """Check if a direct Python tool call is permitted in the current operational mode."""
        if mode == PlannerMode.EXECUTE:
            return True
        if tool_name in self.DEFAULT_ALWAYS_ALLOWED_TOOLS or tool_name in self.ALWAYS_ALLOWED_SUBAGENTS:
            return True
        if tool_name.startswith("return_") or tool_name.endswith("Evaluation") or tool_name.endswith("_response"):
            return True
        allowed_writes = self.ALLOWED_WRITES.get(mode, self.ALLOWED_WRITES[PlannerMode.PLAN])
        return tool_name in allowed_writes


    def is_subagent_allowed(self, subagent_type: str | None, mode: PlannerMode) -> bool:
        """Check if a subagent delegation via the `task` tool is permitted in the current operational mode."""
        if mode == PlannerMode.EXECUTE:
            return True
        if not subagent_type:
            return False
        return subagent_type in self.ALWAYS_ALLOWED_SUBAGENTS

    def _check_permission(self, request: ToolCallRequest) -> ToolMessage | None:
        tool_name = request.tool_call["name"]
        mode = extract_planner_mode(request)

        # In EXECUTE mode, allow all tool calls without any regulation
        if mode == PlannerMode.EXECUTE:
            return None

        # 1. Delegation via `task` tool: passed directly to subagent check
        if tool_name == "task":
            args = request.tool_call.get("args", {})
            subagent_type = args.get("subagent_type") if isinstance(args, dict) else None
            if not self.is_subagent_allowed(subagent_type, mode):
                logger.info(
                    "planner_middleware_subagent_blocked",
                    subagent_type=subagent_type,
                    mode=mode.value,
                )
                return ToolMessage(
                    content=(
                        f"Access Denied: Subagent '{subagent_type}' is restricted in '{mode.value}' mode. "
                        f"In '{mode.value}' mode, you may only consult planning subagents ('sales_manager', 'brain_agent')."
                    ),
                    tool_call_id=request.tool_call["id"],
                    name=tool_name,
                    status="error",
                )
            return None

        # 2. Direct tool invocation check
        if not self.is_tool_allowed(tool_name, mode):
            logger.info(
                "planner_middleware_tool_blocked",
                tool_name=tool_name,
                mode=mode.value,
            )
            return ToolMessage(
                content=(
                    f"Access Denied: Tool '{tool_name}' is mutation-restricted in '{mode.value}' mode. "
                    f"In '{mode.value}' mode, you may only inspect data or execute tools permitted for this phase."
                ),
                tool_call_id=request.tool_call["id"],
                name=tool_name,
                status="error",
            )

        return None

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        err = self._check_permission(request)
        if err is not None:
            return err
        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> ToolMessage | Command:
        print("========================================[Tool Call]========================================")
        print(request.tool_call)
        print("========================================[Tool Call]========================================")

        err = self._check_permission(request)
        if err is not None:
            return err
        return await handler(request)
