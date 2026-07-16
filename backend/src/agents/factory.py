from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from sqlalchemy.ext.asyncio import AsyncSession

from agents.checkpoint_runtime import checkpoint_scope
from agents.middlewares import browser_middlewares, orchestrator_middlewares
from agents.model_provider import resolve_chat_model
from agents.nested_checkpointing import to_checkpointed_compiled_subagent
from agents.runtime import LoopAgentToolContext, build_role_thread_id
from agents.stack_builders import (
    build_company_finder_stack,
    build_contact_finder_stack,
)
from agents.tools import (
    brain_tools,
    company_finder_tools,
    contact_finder_tools,
)
from browser.policy import (
    BrowserPolicyGuard,
    BrowserTaskPolicy,
    policy_enforced_tools,
)
from core.config import get_settings


def _default_backend() -> Any:
    from deepagents.backends import StateBackend

    return StateBackend


def _config(thread_id: str) -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": thread_id}}


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
    return policy_enforced_tools(await load_mcp_tools(browser_session), guard)


def _child_subagent(
    *,
    name: str,
    description: str,
    child_graph: Any,
    effort_prefix: str,
    role_suffix: str,
    parent_role_thread: str,
    registry: dict[str, dict[str, Any]],
) -> Any:
    def list_existing(parent_thread: str) -> list[str]:
        state = registry.get(parent_thread, {})
        active = state.get("active_subagent_threads") or {}
        return [str(item["thread_id"]) for item in active.values() if item.get("thread_id")]

    def load_state(parent_thread: str) -> dict[str, Any]:
        return dict(registry.get(parent_thread) or {"active_subagent_threads": {}})

    def save_state(parent_thread: str, state: dict[str, Any]) -> None:
        registry[parent_thread] = state

    return to_checkpointed_compiled_subagent(
        name=name,
        description=description,
        child_graph=child_graph,
        effort_prefix=effort_prefix,
        allocation_mode="role",
        role_suffix=role_suffix,
        parent_role_thread=parent_role_thread,
        list_existing_thread_ids=list_existing,
        load_parent_state=load_state,
        save_parent_state=save_state,
    )


@asynccontextmanager
async def company_finder_agent_scope(
    session: AsyncSession, strategy_id: str, effort_prefix: str
) -> AsyncIterator[tuple[Any, dict[str, Any]]]:
    """Build Company Finder via stack builders with Browser and Brain compiled subagents."""
    model = resolve_chat_model()
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix="company_finder"
    )
    parent_state_registry: dict[str, dict[str, Any]] = {}
    loop_context = LoopAgentToolContext(
        sales_strategy_id=strategy_id,
        company_id=None,
        effort_prefix=effort_prefix,
    )

    def wrap(name: str, description: str, child: Any, role_suffix: str) -> Any:
        return _child_subagent(
            name=name,
            description=description,
            child_graph=child,
            effort_prefix=effort_prefix,
            role_suffix=role_suffix,
            parent_role_thread=parent_thread,
            registry=parent_state_registry,
        )

    async with checkpoint_scope() as checkpointer, _browser_client().session(
        "playwright"
    ) as browser_session:
        stack = build_company_finder_stack(
            effort_prefix=effort_prefix,
            loop_context=loop_context,
            company_tools=company_finder_tools(session, strategy_id, parent_thread),
            browser_tools=await _browser_tools(browser_session),
            brain_tools=brain_tools(session, strategy_id, "company_finder"),
            checkpointer=checkpointer,
            model=model,
            company_middlewares=orchestrator_middlewares(),
            browser_middlewares=browser_middlewares(),
            wrap_subagent=wrap,
            backend=_default_backend(),
        )
        yield stack.company_finder, _config(parent_thread)


@asynccontextmanager
async def contact_finder_agent_scope(
    session: AsyncSession,
    strategy_id: str,
    company_id: str,
    effort_prefix: str,
) -> AsyncIterator[tuple[Any, dict[str, Any]]]:
    """Build Contact Finder via stack builders with Browser and Brain compiled subagents."""
    model = resolve_chat_model()
    parent_thread = build_role_thread_id(
        effort_prefix=effort_prefix, role_suffix="contact_finder"
    )
    parent_state_registry: dict[str, dict[str, Any]] = {}
    loop_context = LoopAgentToolContext(
        sales_strategy_id=strategy_id,
        company_id=company_id,
        effort_prefix=effort_prefix,
    )

    def wrap(name: str, description: str, child: Any, role_suffix: str) -> Any:
        return _child_subagent(
            name=name,
            description=description,
            child_graph=child,
            effort_prefix=effort_prefix,
            role_suffix=role_suffix,
            parent_role_thread=parent_thread,
            registry=parent_state_registry,
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
            brain_tools=brain_tools(session, strategy_id, "contact_finder"),
            checkpointer=checkpointer,
            model=model,
            contact_middlewares=orchestrator_middlewares(),
            browser_middlewares=browser_middlewares(),
            wrap_subagent=wrap,
            backend=_default_backend(),
        )
        yield stack.contact_finder, _config(parent_thread)
