from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from sqlalchemy.ext.asyncio import AsyncSession

from agents.checkpoint_runtime import checkpoint_scope
from agents.filesystem_backend import (
    default_filesystem_backend,
    default_filesystem_permissions,
)
from agents.middlewares import browser_middlewares, orchestrator_middlewares
from agents.model_provider import resolve_chat_model
from agents.nested_checkpointing import to_checkpointed_compiled_subagent
from agents.parent_state import ParentSubagentStateStore, make_parent_state_callbacks
from agents.runtime import LoopAgentToolContext, build_role_thread_id
from agents.planner_graph import create_planner_graph
from agents.stack_builders import (
    _render_company_responsibility,
    build_company_finder_stack,
    build_contact_finder_stack,
)
from agents.tools import (
    company_finder_tools,
    contact_finder_tools,
    sales_manager_tools,
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
async def company_finder_agent_scope(
    session: AsyncSession,
    strategy_id: str,
    effort_prefix: str,
    *,
    lease_owner: str | None = None,
    is_planner: bool = False,
    role_suffix: str | None = None,
) -> AsyncIterator[tuple[Any, dict[str, Any], ParentSubagentStateStore]]:
    """Build Company Finder / Planner via stack builders with Browser and Brain compiled subagents.

    ``lease_owner`` documents exclusive ownership of the shared operator MCP session.
    The caller must hold a BrowserPool lease before entering this scope.
    """
    _ = lease_owner  # exclusive lock is enforced by BrowserPool; retained for API clarity
    effective_role_suffix = role_suffix or ("planner" if is_planner else "company_finder")
    log.info(
        "company_finder_scope.build_start",
        strategy_id=strategy_id,
        effort_prefix=effort_prefix,
        is_planner=is_planner,
        role_suffix=effective_role_suffix,
    )
    model = resolve_chat_model()
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix=effective_role_suffix
    )
    store = ParentSubagentStateStore(session)
    initial = await store.load(parent_thread)
    store.bind(parent_thread, initial)
    list_existing, load_state, save_state = make_parent_state_callbacks(store, parent_thread)
    loop_context = LoopAgentToolContext(
        sales_strategy_id=strategy_id,
        company_id=None,
        effort_prefix=effort_prefix,
    )
    bundle = (await LoopService(session).bundle(strategy_id)).model_dump(mode="json")

    def wrap(name: str, description: str, child: Any, role_suffix: str, allocation_mode: str = "incremental") -> Any:
        return _child_subagent(
            name=name,
            description=description,
            child_graph=child,
            effort_prefix=effort_prefix,
            role_suffix=role_suffix,
            parent_role_thread=parent_thread,
            list_existing=list_existing,
            load_state=load_state,
            save_state=save_state,
            allocation_mode=allocation_mode,
        )

    log.info(
        "company_finder_scope.browser_mcp_connect",
        strategy_id=strategy_id,
        browser_mcp_url=get_settings().browser_mcp_url,
    )
    async with checkpoint_scope() as checkpointer, _browser_client().session(
        "playwright"
    ) as browser_session:
        log.info("company_finder_scope.stack_build", strategy_id=strategy_id, parent_thread=parent_thread)
        if is_planner:
            planner_graph = create_planner_graph(
                checkpointer=checkpointer,
                model=model,
                effort_prefix=effort_prefix,
                strategy_id=strategy_id,
            )
            try:
                log.info(
                    "company_finder_scope.planner_ready",
                    strategy_id=strategy_id,
                    parent_thread=parent_thread,
                )
                yield planner_graph, _config(parent_thread), store
            finally:
                await store.flush()
                log.info("company_finder_scope.closed", strategy_id=strategy_id, parent_thread=parent_thread)
            return

        company_tools_list = company_finder_tools(session, strategy_id, parent_thread)
        sm_tools = None

        stack = build_company_finder_stack(
            effort_prefix=effort_prefix,
            loop_context=loop_context,
            company_tools=company_tools_list,
            browser_tools=await _browser_tools(browser_session),
            brain_tools=[],
            checkpointer=checkpointer,
            sales_manager_tools=sm_tools,
            model=model,
            company_middlewares=orchestrator_middlewares(),
            browser_middlewares=browser_middlewares(),
            wrap_subagent=wrap,
            backend=default_filesystem_backend(),
            permissions=default_filesystem_permissions(),
            strategy_bundle=bundle,
            is_planner=is_planner,
            role_suffix=effective_role_suffix,
        )
        try:
            log.info(
                "company_finder_scope.ready",
                strategy_id=strategy_id,
                parent_thread=parent_thread,
            )
            yield stack.company_finder, _config(parent_thread), store
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
    """Build Contact Finder via stack builders with Browser and Brain compiled subagents."""
    _ = lease_owner
    model = resolve_chat_model()
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix="contact_finder"
    )
    store = ParentSubagentStateStore(session)
    initial = await store.load(parent_thread)
    store.bind(parent_thread, initial)
    list_existing, load_state, save_state = make_parent_state_callbacks(store, parent_thread)
    loop_context = LoopAgentToolContext(
        sales_strategy_id=strategy_id,
        company_id=company_id,
        effort_prefix=effort_prefix,
    )
    service = LoopService(session)
    bundle = (await service.bundle(strategy_id)).model_dump(mode="json")
    company_payload = (await service.company_detail(strategy_id, company_id)).model_dump(
        mode="json"
    )

    def wrap(name: str, description: str, child: Any, role_suffix: str, allocation_mode: str = "incremental") -> Any:
        return _child_subagent(
            name=name,
            description=description,
            child_graph=child,
            effort_prefix=effort_prefix,
            role_suffix=role_suffix,
            parent_role_thread=parent_thread,
            list_existing=list_existing,
            load_state=load_state,
            save_state=save_state,
            allocation_mode=allocation_mode,
        )

    async with checkpoint_scope() as checkpointer, _browser_client().session(
        "playwright"
    ) as browser_session:
        stack = build_contact_finder_stack(
            effort_prefix=effort_prefix,
            company_id=company_id,
            loop_context=loop_context,
            contact_tools=contact_finder_tools(
                session, strategy_id, company_id, parent_thread
            ),
            browser_tools=await _browser_tools(browser_session),
            brain_tools=[],
            checkpointer=checkpointer,
            model=model,
            contact_middlewares=orchestrator_middlewares(),
            browser_middlewares=browser_middlewares(),
            wrap_subagent=wrap,
            backend=default_filesystem_backend(),
            permissions=default_filesystem_permissions(),
            strategy_bundle=bundle,
            company_payload=company_payload,
        )
        try:
            yield stack.contact_finder, _config(parent_thread), store
        finally:
            await store.flush()
