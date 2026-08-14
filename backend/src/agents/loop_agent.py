"""Planner Agent construction module."""

from __future__ import annotations

from typing import Any

from deepagents import CompiledSubAgent

from langchain_core.language_models import BaseChatModel
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_ollama import ChatOllama
from agents.filesystem_backend import default_filesystem_backend
from agents.planner_middleware import PlannerModeMiddleware
from agents.prompts import (
    BRAIN_AGENT_PROMPT,
    BROWSER_AGENT_PROMPT,
    SALES_MANAGER_PROMPT,
)
from langchain_core.messages.utils import count_tokens_approximately
from langchain.messages import AIMessage
from langgraph.store.base import BaseStore
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain_core.messages import BaseMessage
import structlog
from core.config import Settings, get_settings

logger = structlog.get_logger(__name__)


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
    store: BaseStore = None,
    checkpointer: Any = None,
    backend: Any = None,
) -> Any:
    """Create a LOOP DeepAgent configured with tools and subagents (Brain Agent, Sales Manager, Browser Agent)."""
    effective_tools = list(tools or [])
    effective_subagents = list(subagents or [])
    effective_backend = backend or default_filesystem_backend()

    if strategy_id and not effective_subagents:
        from agents.brain import long_term_memory_tools
        from agents.tools import sales_manager_tools

        # 2. Subagent: Brain Agent (dictionary definition)
        bm_tools = long_term_memory_tools(
            namespace=(strategy_id, "company_finder_planner"),
            store=store,
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
    config = get_settings()

    def token_calculator(messages: list[BaseMessage]) -> int:
        token = 0
        pred_token_count = count_tokens_approximately(messages)
        logger.info(f"Token count prediction: {pred_token_count}")

        token_calc = ChatOllama(
            model=config.model_name,
            base_url=config.model_base_url,
            num_ctx=256000,
            num_predict=1
        )
        for attempt in range(3):
            logger.info(f"Token Calculation Attempt: {attempt}")
            try:
                res = token_calc.invoke(messages)
                if hasattr(res, "usage_metadata") and res.usage_metadata:
                    token = res.usage_metadata.get("input_tokens", 0)
                break
            except Exception as exc:
                logger.warning("token_calculation_failed", error=str(exc))
                token = sum(len(str(getattr(m, "content", ""))) // 4 for m in messages)

        logger.info("tokens_calculated", input_tokens=token)
        return token


    middleware_list = [
        PlannerModeMiddleware(),
        SummarizationMiddleware(
            model=model,
            token_counter=token_calculator,
            trigger=("fraction", 0.1),
        ),
    ]
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
