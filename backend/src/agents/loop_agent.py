"""Planner Agent construction module."""

from __future__ import annotations

from typing import Any

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain.agents import create_agent
from agents.filesystem_backend import default_filesystem_backend
from agents.planner_middleware import PlannerModeMiddleware
from agents.prompts import (
    BRAIN_AGENT_PROMPT,
    BROWSER_AGENT_PROMPT,
    SALES_MANAGER_PROMPT,
)
from deepagents.middleware.subagents import SubAgentMiddleware


def create_loop_agent(
    model: BaseChatModel,
    system_prompt: str | None = None,
    tools: list[Any] | None = None,
    subagents: list[Any] | None = None,
    response_format: Any | None = None,
    name: str = "Company Planner Agent",
    session: Any | None = None,
    strategy_id: str | None = None,
    context_schema=None,
    effort_prefix: str = "",
    store: Any = None,
    checkpointer: Any = None,
    backend: Any = None,
) -> Any:
    """Create a LOOP DeepAgent configured with tools and subagents (Brain Agent, Sales Manager, Browser Agent)."""
    effective_tools = list(tools or [])
    effective_subagents = list(subagents or [])
    effective_backend = backend or default_filesystem_backend()

    if session is not None and strategy_id and not effective_subagents:
        from agents.brain import long_term_memory_tools
        from agents.tools import sales_manager_tools

        # 2. Subagent: Brain Agent (dictionary definition)
        bm_tools = long_term_memory_tools(
            namespace=(strategy_id, "company_finder_planner")
        )
        brain_subagent = {
            "name": "brain_agent",
            "description": "Used to recall past campaign insights, decisions, failures, or persist facts into long-term memory.",
            "system_prompt": BRAIN_AGENT_PROMPT,
            "tools": bm_tools,
            "model": model,
        }

        # 3. Subagent: Sales Manager Agent (dictionary definition)
        sm_tools = sales_manager_tools(session, strategy_id)
        sales_manager_subagent = {
            "name": "sales_manager",
            "description": "Consult for organization background, product offerings, pricing, ICP guidelines, and value propositions.",
            "system_prompt": SALES_MANAGER_PROMPT,
            "tools": sm_tools,
            "model": model,
        }

        # 4. Subagent: Browser Agent (dictionary definition)
        browser_subagent = {
            "name": "browser_agent",
            "description": "Used to execute web searches and browser navigation to audit candidate target companies.",
            "system_prompt": BROWSER_AGENT_PROMPT,
            "tools": [],
            "model": model,
        }

        effective_subagents = [brain_subagent, sales_manager_subagent, browser_subagent]

    middleware_list = [PlannerModeMiddleware()]
    if effective_subagents:
        middleware_list.append(
            SubAgentMiddleware(
                backend=effective_backend,
                subagents=effective_subagents,
            )
        )

    kwargs: dict[str, Any] = {
        "model": model,
        "tools": effective_tools,
        "system_prompt": system_prompt,
        "response_format": response_format,
        "context_schema": context_schema,
        "checkpointer": checkpointer,
        "store": store,
        "name": name,
        "middleware": middleware_list,
    }

    return create_agent(**kwargs)
