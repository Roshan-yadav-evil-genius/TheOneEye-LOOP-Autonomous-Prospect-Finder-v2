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
)
from agents.prompts import (
    BRAIN_AGENT_PROMPT,
    BROWSER_AGENT_PROMPT,
    COMPANY_FINDER_PROMPT,
    CONTACT_FINDER_PROMPT,
    render_prompt,
)
from agents.runtime import (
    LoopAgentToolContext,
    LoopDeepAgentConfig,
    create_loop_deep_agent,
)

WrapSubagent = Callable[[str, str, Any, str], Any]


@dataclass(frozen=True)
class CompanyFinderStack:
    company_finder: Any
    browser: Any
    brain: Any
    effort_prefix: str


@dataclass(frozen=True)
class ContactFinderStack:
    contact_finder: Any
    browser: Any
    brain: Any
    effort_prefix: str
    company_id: str


def _passthrough_wrap(_name: str, _description: str, child: Any, _role_suffix: str) -> Any:
    return child


def _render_company_responsibility(bundle: dict[str, Any] | None) -> str:
    values = company_finder_prompt_values(bundle or {})
    return render_prompt(COMPANY_FINDER_PROMPT, values)


def _render_contact_responsibility(
    bundle: dict[str, Any] | None, company: dict[str, Any] | None
) -> str:
    values = contact_finder_prompt_values(bundle or {}, company)
    return render_prompt(CONTACT_FINDER_PROMPT, values)


def _render_browser_responsibility() -> str:
    return render_prompt(BROWSER_AGENT_PROMPT, browser_prompt_values())


def _render_brain_responsibility() -> str:
    return render_prompt(BRAIN_AGENT_PROMPT, brain_prompt_values())

def build_company_finder_stack(
    *,
    effort_prefix: str,
    loop_context: LoopAgentToolContext,
    company_tools: Sequence[BaseTool],
    browser_tools: Sequence[BaseTool],
    brain_tools: Sequence[BaseTool],
    checkpointer: BaseCheckpointSaver,
    store: BaseStore | None = None,
    model: BaseLanguageModel | None = None,
    company_middlewares: Sequence[AgentMiddleware] | None = None,
    browser_middlewares: Sequence[AgentMiddleware] | None = None,
    wrap_subagent: WrapSubagent | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    permissions: list[FilesystemPermission] | None = None,
    strategy_bundle: dict[str, Any] | None = None,
) -> CompanyFinderStack:
    """Compose Browser + Brain under Company Finder with registration authority checks."""
    wrap = wrap_subagent or _passthrough_wrap
    company_responsibility = _render_company_responsibility(strategy_bundle)
    browser_responsibility = _render_browser_responsibility()
    brain_responsibility = _render_brain_responsibility()

    browser_brain = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Browser Agent Brain",
            responsibility=brain_responsibility,
            tools=brain_tools,
            middlewares=[],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="browser_agent_brain",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
        )
    )
    browser = create_loop_deep_agent(
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
            subagents=[
                wrap(
                    "browser_agent_brain",
                    "Recall and persist Browser Agent long-term memory.",
                    browser_brain,
                    "browser_agent_brain",
                )
            ],
        )
    )
    company_brain = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Company Finder Brain",
            responsibility=brain_responsibility,
            tools=brain_tools,
            middlewares=[],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="company_finder_brain",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
        )
    )
    company_finder = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Company Finder",
            responsibility=company_responsibility,
            tools=company_tools,
            middlewares=company_middlewares or [],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="company_finder",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
            subagents=[
                wrap(
                    "browser_agent",
                    "Perform allowlisted browser research and return evidence.",
                    browser,
                    "browser_agent",
                ),
                wrap(
                    "company_finder_brain",
                    "Recall and persist Company Finder long-term memory.",
                    company_brain,
                    "company_finder_brain",
                ),
            ],
        )
    )
    return CompanyFinderStack(
        company_finder=company_finder,
        browser=browser,
        brain=company_brain,
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
    wrap = wrap_subagent or _passthrough_wrap
    contact_responsibility = _render_contact_responsibility(strategy_bundle, company_payload)
    browser_responsibility = _render_browser_responsibility()
    brain_responsibility = _render_brain_responsibility()

    browser_brain = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Browser Agent Brain",
            responsibility=brain_responsibility,
            tools=brain_tools,
            middlewares=[],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="browser_agent_brain",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
        )
    )
    browser = create_loop_deep_agent(
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
            subagents=[
                wrap(
                    "browser_agent_brain",
                    "Recall and persist Browser Agent long-term memory.",
                    browser_brain,
                    "browser_agent_brain",
                )
            ],
        )
    )
    contact_brain = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Contact Finder Brain",
            responsibility=brain_responsibility,
            tools=brain_tools,
            middlewares=[],
            store=store,
            checkpointer=checkpointer,
            effort_prefix=effort_prefix,
            role_suffix="contact_finder_brain",
            loop_context=loop_context,
            model=model,
            backend=backend,
            permissions=permissions,
        )
    )
    contact_finder = create_loop_deep_agent(
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
            subagents=[
                wrap(
                    "browser_agent",
                    "Research observed LinkedIn profiles and return evidence.",
                    browser,
                    "browser_agent",
                ),
                wrap(
                    "contact_finder_brain",
                    "Recall and persist Contact Finder long-term memory.",
                    contact_brain,
                    "contact_finder_brain",
                ),
            ],
        )
    )
    return ContactFinderStack(
        contact_finder=contact_finder,
        browser=browser,
        brain=contact_brain,
        effort_prefix=effort_prefix,
        company_id=company_id,
    )
