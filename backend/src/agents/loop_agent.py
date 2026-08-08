"""Planner Agent construction module."""

from __future__ import annotations

from typing import Any

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel

from agents.planner_middleware import PlannerModeMiddleware
from agents.prompts import (
    BRAIN_AGENT_PROMPT,
    BROWSER_AGENT_PROMPT,
    COMPANY_FINDER_PLANNER_PROMPT,
    SALES_MANAGER_PROMPT,
)


def create_loop_agent(
    model: BaseChatModel,
    system_prompt: str | None = None,
    tools: list[Any] | None = None,
    subagents: list[Any] | None = None,
    response_format: Any | None = None,
    name: str = "Company Planner Agent",
    session: Any | None = None,
    strategy_id: str | None = None,
    effort_prefix: str = "",
    store: Any = None,
    checkpointer: Any = None,
    backend: Any = None,
) -> Any:
    """Create a LOOP DeepAgent configured with tools and subagents (Brain Agent, Sales Manager, Browser Agent)."""
    effective_tools = list(tools or [])
    effective_subagents = list(subagents or [])

    if session is not None and strategy_id and not effective_subagents:
        from agents.brain import long_term_memory_tools
        from agents.tools import company_finder_tools, sales_manager_tools

        # 1. Strategy retrieval tools for dynamic strategy querying (no hardcoded strategy in code)
        strat_tools = company_finder_tools(session, strategy_id, thread_id=effort_prefix)
        for st in strat_tools:
            if getattr(st, "name", "") in ("get_sales_strategy", "get_sales_strategy_bundle"):
                if st not in effective_tools:
                    effective_tools.append(st)

        # 2. Subagent: Brain Agent (dictionary definition)
        bm_tools = long_term_memory_tools(namespace=(strategy_id, "company_finder_planner"))
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

    kwargs: dict[str, Any] = {
        "model": model,
        "tools": effective_tools,
        "system_prompt": system_prompt,
        "middleware": (PlannerModeMiddleware(),),
        "subagents": effective_subagents,
        "name": name,
        "store":store,
        "backend":backend,
        "checkpointer":checkpointer
    }
    if response_format is not None:
        kwargs["response_format"] = response_format
    return create_deep_agent(**kwargs)

