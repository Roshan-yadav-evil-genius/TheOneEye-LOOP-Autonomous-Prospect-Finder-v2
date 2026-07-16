"""Canonical stack builders from AgentWithBrowser/04-deep-agent-factory.md."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agents.prompts import (
    BRAIN_AGENT_PROMPT,
    BROWSER_AGENT_PROMPT,
    COMPANY_FINDER_PROMPT,
    CONTACT_FINDER_PROMPT,
)
from agents.runtime import (
    LoopAgentToolContext,
    LoopDeepAgentConfig,
    create_loop_deep_agent,
    validate_registration_authority,
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


def build_company_finder_stack(
    *,
    effort_prefix: str,
    loop_context: LoopAgentToolContext,
    company_tools: list[Any],
    browser_tools: list[Any],
    brain_tools: list[Any],
    checkpointer: Any,
    store: Any = None,
    model: Any = None,
    company_middlewares: list[Any] | None = None,
    browser_middlewares: list[Any] | None = None,
    wrap_subagent: WrapSubagent | None = None,
    backend: Any = None,
    permissions: list[Any] | None = None,
) -> CompanyFinderStack:
    """Compose Browser + Brain under Company Finder with registration authority checks."""
    validate_registration_authority(
        "browser_agent", {getattr(tool, "name", str(tool)) for tool in browser_tools}
    )
    validate_registration_authority(
        "company_finder", {getattr(tool, "name", str(tool)) for tool in company_tools}
    )
    wrap = wrap_subagent or _passthrough_wrap

    browser_brain = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Browser Agent Brain",
            responsibility=BRAIN_AGENT_PROMPT,
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
            responsibility=BROWSER_AGENT_PROMPT,
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
            responsibility=BRAIN_AGENT_PROMPT,
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
            responsibility=COMPANY_FINDER_PROMPT,
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
    contact_tools: list[Any],
    browser_tools: list[Any],
    brain_tools: list[Any],
    checkpointer: Any,
    store: Any = None,
    model: Any = None,
    contact_middlewares: list[Any] | None = None,
    browser_middlewares: list[Any] | None = None,
    wrap_subagent: WrapSubagent | None = None,
    backend: Any = None,
    permissions: list[Any] | None = None,
) -> ContactFinderStack:
    """Compose Browser + Brain under Contact Finder for one validated company."""
    validate_registration_authority(
        "browser_agent", {getattr(tool, "name", str(tool)) for tool in browser_tools}
    )
    validate_registration_authority(
        "contact_finder", {getattr(tool, "name", str(tool)) for tool in contact_tools}
    )
    if loop_context.company_id != company_id:
        raise ValueError("Contact Finder stack requires loop_context.company_id == company_id")
    wrap = wrap_subagent or _passthrough_wrap

    browser_brain = create_loop_deep_agent(
        LoopDeepAgentConfig(
            name="Browser Agent Brain",
            responsibility=BRAIN_AGENT_PROMPT,
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
            responsibility=BROWSER_AGENT_PROMPT,
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
            responsibility=BRAIN_AGENT_PROMPT,
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
            responsibility=CONTACT_FINDER_PROMPT,
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
