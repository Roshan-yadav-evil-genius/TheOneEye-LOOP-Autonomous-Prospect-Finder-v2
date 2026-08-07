from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Type
from pydantic import BaseModel, create_model

from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from application.loop_service import LoopService

@dataclass
class SetupChatToolContext:
    organization_id: str
    mode: Literal["ask", "act"]
    service: LoopService
    product_id: str | None = None
    strategy_id: str | None = None


def extract_mode(request: Any) -> str:
    """Extract mode ('ask' or 'act') from ToolCallRequest or its associated config/context."""
    # 1. Direct tool_context on request
    tc = getattr(request, "tool_context", None)
    if tc is not None:
        if hasattr(tc, "mode"):
            return str(tc.mode)
        if isinstance(tc, dict) and "mode" in tc:
            return str(tc["mode"])

    # 2. Config dictionary on request
    config = getattr(request, "config", None)
    if isinstance(config, dict):
        configurable = config.get("configurable", {})
        if isinstance(configurable, dict):
            tc = configurable.get("tool_context")
            if tc is not None:
                if hasattr(tc, "mode"):
                    return str(tc.mode)
                if isinstance(tc, dict) and "mode" in tc:
                    return str(tc["mode"])
            if "mode" in configurable:
                return str(configurable["mode"])

    # 3. Runtime attribute on request
    runtime = getattr(request, "runtime", None)
    if runtime is not None:
        tc = getattr(runtime, "tool_context", getattr(runtime, "context", None))
        if tc is not None:
            if hasattr(tc, "mode"):
                return str(tc.mode)
            if isinstance(tc, dict) and "mode" in tc:
                return str(tc["mode"])
        cfg = getattr(runtime, "config", {})
        if isinstance(cfg, dict):
            tc = cfg.get("configurable", {}).get("tool_context")
            if tc is not None:
                if hasattr(tc, "mode"):
                    return str(tc.mode)
                if isinstance(tc, dict) and "mode" in tc:
                    return str(tc["mode"])

    # 4. Context attribute on request
    ctx = getattr(request, "context", None)
    if ctx is not None:
        if hasattr(ctx, "mode"):
            return str(ctx.mode)
        if isinstance(ctx, dict) and "mode" in ctx:
            return str(ctx["mode"])

    # 5. Direct request dictionary
    if isinstance(request, dict):
        tc = request.get("tool_context")
        if tc is not None and hasattr(tc, "mode"):
            return str(tc.mode)
        if "mode" in request:
            return str(request["mode"])

    return "act"


class ModeMiddleware(AgentMiddleware):
    """Controls tool execution for Form Setup agents based on runtime context mode ('ask' vs 'act')."""

    def _check_permission(self, request: ToolCallRequest) -> ToolMessage | None:
        tool_name = request.tool_call["name"]
        mode = extract_mode(request)

        # In ASK mode, state modification tools (set_*) and write actions are strictly prohibited
        if mode.lower() == "ask":
            if tool_name.startswith("set_") or tool_name.startswith("update_") or tool_name.startswith("delete_"):
                return ToolMessage(
                    content=f"Tool execution prohibited in ASK mode for modification tool '{tool_name}'. Please switch to ACT mode to apply form changes.",
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
        denied = self._check_permission(request)
        if denied:
            return denied
        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> ToolMessage | Command:
        denied = self._check_permission(request)
        if denied:
            return denied
        res = handler(request)
        if hasattr(res, "__await__"):
            return await res
        return res

def build_args_schema(section_key: str, fields: tuple) -> Type[BaseModel]:
    annotations: dict[str, tuple[Type, Any]] = {}
    for f in fields:
        field_type = Any
        if f.kind in ("text", "textarea", "select"):
            field_type = str | None
        elif f.kind == "number":
            field_type = int | None
        elif f.kind == "boolean":
            field_type = bool | None
        elif f.kind in ("string-list", "multi-select"):
            field_type = list[str] | None
        elif f.kind == "object-list":
            field_type = list[dict[str, Any]] | None

        if f.path == ".":
            annotations["items"] = (list[Any] | None, None)
        else:
            annotations[f.path.replace(".", "_")] = (field_type, None)

    return create_model(f"Set{section_key.title().replace('_', '')}Schema", **annotations)

