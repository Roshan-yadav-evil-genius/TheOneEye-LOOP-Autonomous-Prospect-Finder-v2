"""LOOP deep-agent factory configuration and compiled graph materialization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


def build_role_thread_id(*, effort_prefix: str, role_suffix: str) -> str:
    return f"{effort_prefix}_{role_suffix}"


def build_company_effort_prefix(product_id: str, strategy_id: str, effort_seq: int) -> str:
    return f"LOOP_{product_id}_{strategy_id}_{effort_seq}"


def build_contact_effort_prefix(
    product_id: str,
    strategy_id: str,
    sales_strategy_attempt_at_register: int,
    company_id: str,
    contact_effort_seq: int,
) -> str:
    return (
        f"LOOP_{product_id}_{strategy_id}_{sales_strategy_attempt_at_register}_"
        f"{company_id}_{contact_effort_seq}"
    )


def allocate_gpa_thread_id(parent_role_thread: str, existing_thread_ids: list[str]) -> str:
    pattern = re.compile(rf"^{re.escape(parent_role_thread)}_GPA_(\d+)$")
    numbers = [
        int(match.group(1)) for value in existing_thread_ids if (match := pattern.match(value))
    ]
    return f"{parent_role_thread}_GPA_{max(numbers, default=0) + 1}"


class AgentGraph(Protocol):
    async def ainvoke(self, value: Any, config: dict[str, Any]) -> Any: ...

    async def aget_state(self, config: dict[str, Any]) -> Any: ...


@dataclass(frozen=True)
class LoopAgentToolContext:
    sales_strategy_id: str
    company_id: str | None
    effort_prefix: str


@dataclass
class LoopDeepAgentConfig:
    name: str
    responsibility: str
    tools: list[Any]
    middlewares: list[Any]
    store: Any
    checkpointer: Any
    effort_prefix: str
    role_suffix: str
    loop_context: LoopAgentToolContext
    model: Any = None
    subagents: list[Any] = field(default_factory=list)
    backend: Any = None
    permissions: list[Any] | None = None


@dataclass
class ConfiguredAgent:
    """Provider-neutral factory plan used by dry-run stack builders and tests."""

    config: LoopDeepAgentConfig
    thread_id: str
    system_prompt: str


def assemble_system_prompt(*, name: str, responsibility: str) -> str:
    return f"You are {name}.\n{responsibility}".strip()


def create_loop_deep_agent(config: LoopDeepAgentConfig) -> Any:
    """Build either a ConfiguredAgent plan (no model) or a compiled deepagents graph."""
    system_prompt = assemble_system_prompt(
        name=config.name, responsibility=config.responsibility
    )
    thread_id = build_role_thread_id(
        effort_prefix=config.effort_prefix, role_suffix=config.role_suffix
    )
    if config.model is None:
        return ConfiguredAgent(config=config, thread_id=thread_id, system_prompt=system_prompt)
    kwargs: dict[str, Any] = {
        "model": config.model,
        "tools": config.tools,
        "system_prompt": system_prompt,
        "middleware": tuple(config.middlewares),
        "subagents": config.subagents,
        "checkpointer": config.checkpointer,
        "store": config.store,
        "name": config.name,
    }
    if config.backend is not None:
        kwargs["backend"] = config.backend
    if config.permissions is not None:
        kwargs["permissions"] = config.permissions
    return create_deep_agent(**kwargs)


def build_loop_agent_graph(
    *,
    model: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str,
    checkpointer: Any,
    store: Any | None = None,
    subagents: list[Any] | None = None,
    middleware: list[Any] | None = None,
    backend: Any = None,
    permissions: list[Any] | None = None,
    name: str | None = None,
) -> Any:
    """Build a real deepagents graph; callers own PostgreSQL checkpoint resources."""
    kwargs: dict[str, Any] = {
        "model": model,
        "tools": tools,
        "system_prompt": system_prompt,
        "checkpointer": checkpointer,
        "store": store,
        "subagents": subagents or [],
        "middleware": tuple(middleware or ()),
        "name": name,
    }
    if backend is not None:
        kwargs["backend"] = backend
    if permissions is not None:
        kwargs["permissions"] = permissions
    return create_deep_agent(**kwargs)


async def invoke_compiled_child_until_idle(child: AgentGraph, *, thread_id: str, task: Any) -> Any:
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await child.aget_state(config)
    pending = bool(getattr(snapshot, "next", ()))
    result = await child.ainvoke(None if pending else task, config)
    while True:
        snapshot = await child.aget_state(config)
        if not getattr(snapshot, "next", ()):
            return result
        result = await child.ainvoke(None, config)


COMPANY_FINDER_TOOLS = {
    "get_sales_strategy_bundle",
    "register_company",
    "set_scratch_pad",
}
CONTACT_FINDER_TOOLS = {
    "get_sales_strategy_bundle",
    "get_company",
    "is_profile_present",
    "register_contact",
    "blacklist_prospect",
    "set_scratch_pad",
}
BROWSER_TOOLS = {
    "navigate",
    "inspect",
    "click",
    "type",
    "is_profile_present",
}


def validate_registration_authority(role_suffix: str, tool_names: set[str]) -> None:
    if role_suffix == "browser_agent" and {"register_company", "register_contact"} & tool_names:
        raise ValueError("Browser agents may not receive registration tools.")
    if role_suffix == "company_finder" and "register_contact" in tool_names:
        raise ValueError("Company Finder may not register contacts.")
    if role_suffix == "contact_finder" and "register_company" in tool_names:
        raise ValueError("Contact Finder may not register companies.")
