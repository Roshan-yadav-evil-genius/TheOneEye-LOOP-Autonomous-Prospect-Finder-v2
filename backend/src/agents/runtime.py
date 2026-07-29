"""LOOP deep-agent factory configuration and compiled graph materialization."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from deepagents import (
    AsyncSubAgent,
    CompiledSubAgent,
    FilesystemPermission,
    SubAgent,
    create_deep_agent,
)
from deepagents.backends.protocol import BackendFactory, BackendProtocol
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore


def validate_registration_authority(agent_role: str, tool_names: set[str]) -> None:
    if "browser" in agent_role and ("register_company" in tool_names or "register_contact" in tool_names):
        raise ValueError("Browser agent cannot possess registration tools")
    if agent_role == "company_finder" and "register_contact" in tool_names:
        raise ValueError("Company finder cannot register contact")
    if agent_role == "contact_finder" and "register_company" in tool_names:
        raise ValueError("Contact finder cannot register company")


def build_role_thread_id(*, effort_prefix: str, role_suffix: str) -> str:
    return f"{effort_prefix}_{role_suffix}"


def build_org_setup_thread_id(organization_id: str) -> str:
    return f"LOOP_{organization_id}_org_setup_chat_1"


def build_product_setup_thread_id(organization_id: str, product_id: str) -> str:
    return f"LOOP_{organization_id}_{product_id}_product_setup_chat_1"


def build_strategy_setup_thread_id(organization_id: str, product_id: str, strategy_id: str) -> str:
    return f"LOOP_{organization_id}_{product_id}_{strategy_id}_strategy_setup_chat_1"


def allocate_next_setup_thread_id(base_thread_id: str, existing_thread_ids: list[str]) -> str:
    """Return the next sequenced setup-chat thread ID.

    Every setup thread ID includes a sequence suffix (``_<n>``), starting with
    ``_1`` for the initial thread.

        LOOP_{org}_org_setup_chat_1      → seq 1
        LOOP_{org}_org_setup_chat_2      → seq 2
        LOOP_{org}_org_setup_chat_3      → seq 3
        ...

    Callers must include all known thread IDs (including any still-running ones)
    in *existing_thread_ids* to avoid gaps or conflicts.
    """
    stem = re.sub(r"_\d+$", "", base_thread_id)
    pattern = re.compile(rf"^{re.escape(stem)}_(\d+)$")
    numbers: list[int] = []
    for tid in existing_thread_ids:
        if tid == stem:
            numbers.append(1)
        elif m := pattern.match(tid):
            numbers.append(int(m.group(1)))
    next_seq = max(numbers, default=0) + 1
    return f"{stem}_{next_seq}"



def build_company_effort_prefix(org_id: str, product_id: str, strategy_id: str, effort_seq: int) -> str:
    return f"LOOP_{org_id}_{product_id}_{strategy_id}_{effort_seq}"


def build_contact_effort_prefix(
    org_id: str,
    product_id: str,
    strategy_id: str,
    sales_strategy_attempt_at_register: int,
    company_id: str,
    contact_effort_seq: int,
) -> str:
    return (
        f"LOOP_{org_id}_{product_id}_{strategy_id}_{sales_strategy_attempt_at_register}_"
        f"{company_id}_{contact_effort_seq}"
    )


def allocate_incremental_thread_id(parent_role_thread: str, existing_thread_ids: list[str], suffix: str) -> str:
    """Allocate next incremental id; callers must supply a concurrency-safe existing id list."""
    pattern = re.compile(rf"^{re.escape(parent_role_thread)}_{re.escape(suffix)}_(\d+)$")
    numbers = [
        int(match.group(1)) for value in existing_thread_ids if (match := pattern.match(value))
    ]
    # Never skip past a still-running agent: callers must include running ids in existing.
    return f"{parent_role_thread}_{suffix}_{max(numbers, default=0) + 1}"


def collect_incremental_thread_ids(
    parent_role_thread: str, active_subagent_threads: dict[str, Any], suffix: str
) -> list[str]:
    """Gather incremental thread ids from durable parent state for max+1 allocation."""
    pattern = re.compile(rf"^{re.escape(parent_role_thread)}_{re.escape(suffix)}_\d+$")
    found: list[str] = []
    for item in (active_subagent_threads or {}).values():
        thread_id = str(item.get("thread_id") or "")
        if pattern.match(thread_id):
            found.append(thread_id)
    return found


def allocate_gpa_thread_id_from_state(
    parent_role_thread: str, parent_state: dict[str, Any]
) -> str:
    active = dict(parent_state.get("active_subagent_threads") or {})
    # Reuse any still-running GPA instead of allocating a new number.
    for item in active.values():
        if item.get("status") == "running" and str(item.get("thread_id", "")).startswith(
            f"{parent_role_thread}_GPA_"
        ):
            return str(item["thread_id"])
    existing = collect_gpa_thread_ids(parent_role_thread, active)
    return allocate_gpa_thread_id(parent_role_thread, existing)


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
    tools: Sequence[BaseTool]
    middlewares: Sequence[AgentMiddleware]
    store: BaseStore | None
    checkpointer: BaseCheckpointSaver
    effort_prefix: str
    role_suffix: str
    loop_context: LoopAgentToolContext
    model: BaseChatModel | None = None
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None
    backend: BackendProtocol | BackendFactory | None = None
    permissions: list[FilesystemPermission] | None = None
    brain_tools: Sequence[BaseTool] | None = None
    brain_responsibility: str | None = None
    wrap_subagent: Any | None = None
    brain_persistent: bool = True


@dataclass
class ConfiguredAgent:
    """Provider-neutral factory plan used by dry-run stack builders and tests."""

    config: LoopDeepAgentConfig
    thread_id: str
    system_prompt: str


def assemble_system_prompt(*, name: str, responsibility: str) -> str:
    return f"You are {name}.\n{responsibility}".strip()


def create_deep_agent_with_brain(config: LoopDeepAgentConfig) -> Any:
    """Build either a ConfiguredAgent plan (no model) or a compiled deepagents graph."""
    system_prompt = assemble_system_prompt(
        name=config.name, responsibility=config.responsibility
    )
    thread_id = build_role_thread_id(
        effort_prefix=config.effort_prefix, role_suffix=config.role_suffix
    )
    if config.model is None:
        return ConfiguredAgent(config=config, thread_id=thread_id, system_prompt=system_prompt)
    subagents_list = list(config.subagents) if config.subagents else []
    wrap = config.wrap_subagent if config.wrap_subagent is not None else lambda n, d, c, rs, mode="incremental": c
    
    is_internal = config.role_suffix.endswith("_brain") or config.role_suffix.endswith("_gpa")
    
    if not is_internal and config.brain_tools is not None and config.brain_responsibility is not None:
        brain_mode = "role" if config.brain_persistent else "incremental"
        brain_config = LoopDeepAgentConfig(
            name=f"{config.name} Brain",
            responsibility=config.brain_responsibility,
            tools=config.brain_tools,
            middlewares=[],
            store=config.store,
            checkpointer=config.checkpointer,
            effort_prefix=config.effort_prefix,
            role_suffix=f"{config.role_suffix}_brain",
            loop_context=config.loop_context,
            model=config.model,
            backend=config.backend,
            permissions=config.permissions,
        )
        brain_agent = create_deep_agent_with_brain(brain_config)
        subagents_list.append(
            wrap(
                f"{config.role_suffix}_brain",
                f"Recall and persist {config.name} long-term memory.",
                brain_agent,
                f"{config.role_suffix}_brain",
                brain_mode,
            )
        )
        
    if not is_internal:
        gpa_config = LoopDeepAgentConfig(
            name="General Purpose Agent",
            responsibility="You are a general-purpose delegate agent responsible for context management and tool execution on behalf of the main agent.",
            tools=config.tools,
            middlewares=config.middlewares,
            subagents=list(subagents_list),
            store=config.store,
            checkpointer=config.checkpointer,
            effort_prefix=config.effort_prefix,
            role_suffix=f"{config.role_suffix}_gpa",
            loop_context=config.loop_context,
            model=config.model,
            backend=config.backend,
            permissions=config.permissions,
        )
        gpa_agent = create_deep_agent_with_brain(gpa_config)
        subagents_list.append(
            wrap(
                "general-purpose",
                "General purpose task delegation.",
                gpa_agent,
                f"{config.role_suffix}_gpa",
                "incremental",
            )
        )

    kwargs: dict[str, Any] = {
        "model": config.model,
        "tools": config.tools,
        "system_prompt": system_prompt,
        "middleware": tuple(config.middlewares),
        "subagents": subagents_list,
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
    tools: Sequence[BaseTool],
    system_prompt: str,
    checkpointer: BaseCheckpointSaver,
    store: BaseStore | None = None,
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    middleware: Sequence[AgentMiddleware] | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    permissions: list[FilesystemPermission] | None = None,
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


