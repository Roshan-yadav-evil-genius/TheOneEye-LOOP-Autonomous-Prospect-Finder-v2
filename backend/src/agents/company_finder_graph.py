"""Company Finder StateGraph workflow module.

Encapsulates company finder agent state in a LangGraph StateGraph, compiled with
a checkpointer and invoked via streaming using thread configurations.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Optional

import structlog
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

logger = structlog.get_logger(__name__)


def create_company_finder_graph(
    model: Any | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    store: Any | None = None,
    effort_prefix: str = "",
    strategy_id: str | None = None,
    session: Any | None = None,
) -> CompiledStateGraph:
    """Build a StateGraph workflow for Company Finder."""

    async def mock_company_finder(state: MessagesState) -> dict[str, Any]:
        logger.info("company_finder_node_executing", effort_prefix=effort_prefix)
        return {
            "messages": [
                AIMessage(content="Company Finder execution completed placeholder.")
            ]
        }

    builder = StateGraph(MessagesState)
    builder.add_node("mock_company_finder", mock_company_finder)
    builder.add_edge(START, "mock_company_finder")
    builder.add_edge("mock_company_finder", END)

    return builder.compile(checkpointer=checkpointer)


async def stream_company_finder_graph(
    graph: CompiledStateGraph,
    input_data: Any,
    thread_id: str,
    version: str = "v2",
) -> AsyncIterator[dict[str, Any]]:
    """Invoke the compiled company finder graph through stream."""
    from core.config import get_settings

    config = {
        "recursion_limit": get_settings().agent_recursion_limit,
        "configurable": {
            "thread_id": thread_id,
        },
    }
    async for event in graph.astream_events(
        input_data, config=config, version=version, subgraphs=True
    ):
        yield event
