"""Contact Finder StateGraph workflow module.

Encapsulates contact finder agent state in a LangGraph StateGraph, compiled with
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


def create_contact_finder_graph(
    model: Any | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    store: Any | None = None,
    effort_prefix: str = "",
    strategy_id: str | None = None,
    company_id: str | None = None,
    session: Any | None = None,
) -> CompiledStateGraph:
    """Build a StateGraph workflow for Contact Finder."""

    async def mock_contact_finder(state: MessagesState) -> dict[str, Any]:
        logger.info("contact_finder_node_executing", effort_prefix=effort_prefix, company_id=company_id)
        return {
            "messages": [
                AIMessage(content="Contact Finder execution completed placeholder.")
            ]
        }

    builder = StateGraph(MessagesState)
    builder.add_node("mock_contact_finder", mock_contact_finder)
    builder.add_edge(START, "mock_contact_finder")
    builder.add_edge("mock_contact_finder", END)

    return builder.compile(checkpointer=checkpointer)


async def stream_contact_finder_graph(
    graph: CompiledStateGraph,
    input_data: Any,
    thread_id: str,
    version: str = "v2",
) -> AsyncIterator[dict[str, Any]]:
    """Invoke the compiled contact finder graph through stream."""
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
