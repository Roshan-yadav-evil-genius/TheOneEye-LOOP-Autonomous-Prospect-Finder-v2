"""Canonical stack builders from AgentWithBrowser/04-deep-agent-factory.md."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from deepagents import FilesystemPermission
from deepagents.backends.protocol import BackendFactory, BackendProtocol
from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import BaseTool

from agents.prompt_context import (
    browser_prompt_values,
    brain_prompt_values,
    company_finder_prompt_values,
    contact_finder_prompt_values,
    sales_manager_prompt_values,
)
from agents.prompts import (
    BRAIN_AGENT_PROMPT,
    BROWSER_AGENT_PROMPT,
    COMPANY_FINDER_PLANNER_PROMPT,
    COMPANY_FINDER_PROMPT,
    CONTACT_FINDER_PROMPT,
    SALES_MANAGER_PROMPT,
    render_prompt,
)
from typing import Any, Callable, Protocol, Sequence
from agents.runtime import (
    LoopAgentToolContext,
    LoopDeepAgentConfig,
    create_deep_agent_with_brain,
    validate_registration_authority,
)

class WrapSubagent(Protocol):
    def __call__(
        self,
        name: str,
        description: str,
        child: Any,
        role_suffix: str,
        allocation_mode: str = "incremental",
    ) -> Any: ...


@dataclass(frozen=True)
class CompanyFinderStack:
    company_finder: Any
    browser: Any
    effort_prefix: str
    sales_manager: Any | None = None


@dataclass(frozen=True)
class ContactFinderStack:
    contact_finder: Any
    browser: Any
    effort_prefix: str
    company_id: str


def _passthrough_wrap(_name: str, _description: str, child: Any, _role_suffix: str, _allocation_mode: str = "incremental") -> Any:
    return child


def _render_company_responsibility(
    bundle: dict[str, Any] | None, is_planner: bool = False
) -> str:
    values = company_finder_prompt_values(bundle or {})
    prompt_template = COMPANY_FINDER_PLANNER_PROMPT if is_planner else COMPANY_FINDER_PROMPT
    return render_prompt(prompt_template, values)


def _render_contact_responsibility(
    bundle: dict[str, Any] | None, company: dict[str, Any] | None
) -> str:
    values = contact_finder_prompt_values(bundle or {}, company)
    return render_prompt(CONTACT_FINDER_PROMPT, values)


def _render_browser_responsibility() -> str:
    return render_prompt(BROWSER_AGENT_PROMPT, browser_prompt_values())


def _render_brain_responsibility() -> str:
    return render_prompt(BRAIN_AGENT_PROMPT, brain_prompt_values())


def _render_sales_manager_responsibility() -> str:
    return render_prompt(SALES_MANAGER_PROMPT, sales_manager_prompt_values())


def _tool_names(tools: Sequence[BaseTool]) -> set[str]:
    return {getattr(t, "name", str(t)) for t in tools}


def build_company_finder_stack(
    *,
    effort_prefix: str,
    loop_context: LoopAgentToolContext,
    company_tools: Sequence[BaseTool],
    browser_tools: Sequence[BaseTool],
    brain_tools: Sequence[BaseTool],
    checkpointer: BaseCheckpointSaver,
    sales_manager_tools: Sequence[BaseTool] | None = None,
    store: BaseStore | None = None,
    model: BaseLanguageModel | None = None,
    company_middlewares: Sequence[AgentMiddleware] | None = None,
    browser_middlewares: Sequence[AgentMiddleware] | None = None,
    wrap_subagent: WrapSubagent | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    permissions: list[FilesystemPermission] | None = None,
    strategy_bundle: dict[str, Any] | None = None,
    is_planner: bool = False,
    role_suffix: str | None = None,
) -> CompanyFinderStack:
    """Compose Browser + Brain + Sales Manager under Company Finder/Planner with registration authority checks."""
    validate_registration_authority("browser_agent", _tool_names(browser_tools))
    validate_registration_authority("company_finder", _tool_names(company_tools))
    wrap = wrap_subagent or _passthrough_wrap
    effective_role_suffix = role_suffix or ("planner" if is_planner else "company_finder")
    company_responsibility = _render_company_responsibility(strategy_bundle, is_planner=is_planner)
    browser_responsibility = _render_browser_responsibility()
    brain_responsibility = _render_brain_responsibility()

    browser = create_deep_agent_with_brain(
        LoopDeepAgentConfig(
            name="Browser Agent",
            responsibility=browser_responsibility,
            tools=browser_tools,
            middlewares=browser_middlewares or [],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="browser_agent",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
            brain_tools=brain_tools,
            brain_responsibility=brain_responsibility,
            wrap_subagent=wrap,
        )
    )

    subagents = []
    sales_manager_agent = None
    if is_planner and sales_manager_tools is not None:
        sales_manager_responsibility = _render_sales_manager_responsibility()
        sales_manager_agent = create_deep_agent_with_brain(
            LoopDeepAgentConfig(
                name="Sales Manager",
                responsibility=sales_manager_responsibility,
                tools=sales_manager_tools,
                middlewares=company_middlewares or [],
                store=store,
                checkpointer=checkpointer,
                effort_prefix=effort_prefix,
                role_suffix="sales_manager",
                loop_context=loop_context,
                model=model,
                backend=backend,
                permissions=permissions,
                brain_tools=brain_tools,
                brain_responsibility=brain_responsibility,
                wrap_subagent=wrap,
            )
        )
        subagents.append(
            wrap(
                "sales_manager",
                "Consult for organization domain background, product offerings, value propositions, and ICP guidance.",
                sales_manager_agent,
                "sales_manager",
            )
        )

    if not is_planner:
        subagents.append(
            wrap(
                "browser_agent",
                "Perform allowlisted browser research and return evidence.",
                browser,
                "browser_agent",
            )
        )

    company_finder = create_deep_agent_with_brain(
        LoopDeepAgentConfig(
            name="Company Planner" if is_planner else "Company Finder",
            responsibility=company_responsibility,
            tools=company_tools,
            middlewares=company_middlewares or [],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix=effective_role_suffix,
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
            brain_tools=brain_tools,
            brain_responsibility=brain_responsibility,
            wrap_subagent=wrap,
            subagents=subagents,
        )
    )
    return CompanyFinderStack(
        company_finder=company_finder,
        browser=browser,
        sales_manager=sales_manager_agent,
        effort_prefix=effort_prefix,
    )



def build_contact_finder_stack(
    *,
    effort_prefix: str,
    company_id: str,
    loop_context: LoopAgentToolContext,
    contact_tools: Sequence[BaseTool],
    browser_tools: Sequence[BaseTool],
    brain_tools: Sequence[BaseTool],
    checkpointer: BaseCheckpointSaver,
    store: BaseStore | None = None,
    model: BaseLanguageModel | None = None,
    contact_middlewares: Sequence[AgentMiddleware] | None = None,
    browser_middlewares: Sequence[AgentMiddleware] | None = None,
    wrap_subagent: WrapSubagent | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    permissions: list[FilesystemPermission] | None = None,
    strategy_bundle: dict[str, Any] | None = None,
    company_payload: dict[str, Any] | None = None,
) -> ContactFinderStack:
    """Compose Browser + Brain under Contact Finder for one validated company."""
    if loop_context.company_id != company_id:
        raise ValueError("Contact Finder stack requires loop_context.company_id == company_id")
    validate_registration_authority("browser_agent", _tool_names(browser_tools))
    validate_registration_authority("contact_finder", _tool_names(contact_tools))
    wrap = wrap_subagent or _passthrough_wrap
    contact_responsibility = _render_contact_responsibility(strategy_bundle, company_payload)
    browser_responsibility = _render_browser_responsibility()
    brain_responsibility = _render_brain_responsibility()

    browser = create_deep_agent_with_brain(
        LoopDeepAgentConfig(
            name="Browser Agent",
            responsibility=browser_responsibility,
            tools=browser_tools,
            middlewares=browser_middlewares or [],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="browser_agent",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
            brain_tools=brain_tools,
            brain_responsibility=brain_responsibility,
            wrap_subagent=wrap,
        )
    )
    contact_finder = create_deep_agent_with_brain(
        LoopDeepAgentConfig(
            name="Contact Finder",
            responsibility=contact_responsibility,
            tools=contact_tools,
            middlewares=contact_middlewares or [],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="contact_finder",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
            brain_tools=brain_tools,
            brain_responsibility=brain_responsibility,
            wrap_subagent=wrap,
            subagents=[
                wrap(
                    "browser_agent",
                    "Research observed LinkedIn profiles and return evidence.",
                    browser,
                    "browser_agent",
                ),
            ],
        )
    )
    return ContactFinderStack(
        contact_finder=contact_finder,
        browser=browser,
        effort_prefix=effort_prefix,
        company_id=company_id,
    )
