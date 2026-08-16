from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from sqlalchemy.ext.asyncio import AsyncSession

from agents.checkpoint_runtime import checkpoint_and_store_scope, checkpoint_scope
from agents.filesystem_backend import (
    default_filesystem_backend,
    default_filesystem_permissions,
)
from agents.middlewares import browser_middlewares, orchestrator_middlewares
from agents.model_provider import resolve_chat_model
from agents.nested_checkpointing import to_checkpointed_compiled_subagent
from agents.parent_state import ParentSubagentStateStore, make_parent_state_callbacks
from agents.runtime import LoopAgentToolContext, build_role_thread_id
from agents.company_finder_graph import create_company_finder_graph
from agents.contact_finder_graph import create_contact_finder_graph
from agents.planner_graph import create_planner_graph
from agents.stack_builders import (
    _render_company_responsibility,
    build_company_finder_stack,
    build_contact_finder_stack,
)
from agents.tools import (
    contact_finder_tools,
    get_register_company_tool,
)
from application.loop_service import LoopService
from browser.policy import (
    BrowserPolicyGuard,
    BrowserTaskPolicy,
    policy_enforced_tools,
)
from core.config import get_settings
from observability.logging import get_logger

log = get_logger("loop.factory")


def _config(thread_id: str) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": get_settings().agent_recursion_limit,
    }


def _browser_client() -> MultiServerMCPClient:
    connection: Any = {
        "transport": "http",
        "url": get_settings().browser_mcp_url,
    }
    return MultiServerMCPClient({"playwright": connection})


async def _browser_tools(browser_session: Any) -> list[Any]:
    settings = get_settings()
    domains = frozenset(
        part.strip().lower()
        for part in settings.browser_allowed_domains.split(",")
        if part.strip()
    )
    guard = BrowserPolicyGuard(
        BrowserTaskPolicy(
            allowed_domains=domains,
            minimum_action_interval_seconds=settings.browser_action_interval_seconds,
        )
    )
    tools = policy_enforced_tools(await load_mcp_tools(browser_session), guard)
    # Registration authority: browser never receives register_* even if MCP misconfigured.
    return [
        tool
        for tool in tools
        if getattr(tool, "name", "") not in {"register_company", "register_contact"}
    ]


def _child_subagent(
    *,
    name: str,
    description: str,
    child_graph: Any,
    effort_prefix: str,
    role_suffix: str,
    parent_role_thread: str,
    list_existing: Any,
    load_state: Any,
    save_state: Any,
    allocation_mode: str = "role",
) -> Any:
    return to_checkpointed_compiled_subagent(
        name=name,
        description=description,
        child_graph=child_graph,
        effort_prefix=effort_prefix,
        allocation_mode=allocation_mode,  # type: ignore[arg-type]
        role_suffix=role_suffix,
        parent_role_thread=parent_role_thread,
        list_existing_thread_ids=list_existing,
        load_parent_state=load_state,
        save_parent_state=save_state,
    )


@asynccontextmanager
async def planner_graph_agent_scope(
    session: AsyncSession,
    strategy_id: str,
    effort_prefix: str,
) -> AsyncIterator[tuple[Any, dict[str, Any], ParentSubagentStateStore]]:
    """Build Planner StateGraph workflow agent scope.

    Operates strictly on strategy DB data and LLM subagents without acquiring Playwright browser sessions.
    """
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix="planner"
    )
    log.info(
        "planner_graph_scope.build_start",
        strategy_id=strategy_id,
        effort_prefix=effort_prefix,
        parent_thread=parent_thread,
    )
    model = resolve_chat_model()
    store = ParentSubagentStateStore(session)
    initial = await store.load(parent_thread)
    store.bind(parent_thread, initial)

    async with checkpoint_and_store_scope() as (checkpointer, mem_store):
        planner_graph = create_planner_graph(
            checkpointer=checkpointer,
            store=mem_store,
            model=model,
            effort_prefix=effort_prefix,
            strategy_id=strategy_id,
            session=session,
        )
        try:
            log.info(
                "planner_graph_scope.ready",
                strategy_id=strategy_id,
                parent_thread=parent_thread,
            )
            yield planner_graph, _config(parent_thread), store
        finally:
            await store.flush()
            log.info("planner_graph_scope.closed", strategy_id=strategy_id, parent_thread=parent_thread)


@asynccontextmanager
async def company_finder_agent_scope(
    session: AsyncSession,
    strategy_id: str,
    effort_prefix: str,
    *,
    lease_owner: str | None = None,
) -> AsyncIterator[tuple[Any, dict[str, Any], ParentSubagentStateStore]]:
    """Build Company Finder StateGraph workflow agent scope.

    Operates strictly on state graph workflow compiled with checkpointer.
    """
    _ = lease_owner
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix="company_finder"
    )
    log.info(
        "company_finder_scope.build_start",
        strategy_id=strategy_id,
        effort_prefix=effort_prefix,
        parent_thread=parent_thread,
    )
    model = resolve_chat_model()
    store = ParentSubagentStateStore(session)
    initial = await store.load(parent_thread)
    store.bind(parent_thread, initial)

    async with checkpoint_and_store_scope() as (checkpointer, mem_store):
        company_graph = create_company_finder_graph(
            model=model,
            checkpointer=checkpointer,
            store=mem_store,
            effort_prefix=effort_prefix,
            strategy_id=strategy_id,
            session=session,
        )
        try:
            log.info(
                "company_finder_scope.ready",
                strategy_id=strategy_id,
                parent_thread=parent_thread,
            )
            yield company_graph, _config(parent_thread), store
        finally:
            await store.flush()
            log.info("company_finder_scope.closed", strategy_id=strategy_id, parent_thread=parent_thread)


@asynccontextmanager
async def contact_finder_agent_scope(
    session: AsyncSession,
    strategy_id: str,
    company_id: str,
    effort_prefix: str,
    *,
    lease_owner: str | None = None,
) -> AsyncIterator[tuple[Any, dict[str, Any], ParentSubagentStateStore]]:
    """Build Contact Finder StateGraph workflow agent scope."""
    _ = lease_owner
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix="contact_finder"
    )
    log.info(
        "contact_finder_scope.build_start",
        strategy_id=strategy_id,
        company_id=company_id,
        effort_prefix=effort_prefix,
        parent_thread=parent_thread,
    )
    model = resolve_chat_model()
    store = ParentSubagentStateStore(session)
    initial = await store.load(parent_thread)
    store.bind(parent_thread, initial)

    async with checkpoint_and_store_scope() as (checkpointer, mem_store):
        contact_graph = create_contact_finder_graph(
            model=model,
            checkpointer=checkpointer,
            store=mem_store,
            effort_prefix=effort_prefix,
            strategy_id=strategy_id,
            company_id=company_id,
            session=session,
        )
        try:
            log.info(
                "contact_finder_scope.ready",
                strategy_id=strategy_id,
                company_id=company_id,
                parent_thread=parent_thread,
            )
            yield contact_graph, _config(parent_thread), store
        finally:
            await store.flush()
            log.info("contact_finder_scope.closed", strategy_id=strategy_id, parent_thread=parent_thread)
