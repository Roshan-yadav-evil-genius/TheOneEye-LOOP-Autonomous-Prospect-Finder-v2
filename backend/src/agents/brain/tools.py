"""LangMem tool factory for Brain Agent long-term memory."""

from typing import List, Optional

from langchain_core.tools import StructuredTool
from langgraph.store.base import BaseStore
from langmem import create_manage_memory_tool, create_search_memory_tool

from agents.brain.prompts import (
    ACTION_INSTRUCTIONS,
    ACTION_SEARCH_INSTRUCTIONS,
    DECISION_INSTRUCTIONS,
    DECISION_SEARCH_INSTRUCTIONS,
    FAILURE_INSTRUCTIONS,
    FAILURE_SEARCH_INSTRUCTIONS,
    INSIGHT_INSTRUCTIONS,
    INSIGHT_SEARCH_INSTRUCTIONS,
)


def memory_tool(
    memory_type: str,
    namespace: tuple[str, ...] | str,
    instruction: str,
    search_instruction: str,
    store: Optional[BaseStore] = None,
):
    manage = create_manage_memory_tool(
        name=f"manage_{memory_type}_memory",
        namespace=namespace,
        instructions=instruction,
        store=store,
    )

    search = create_search_memory_tool(
        name=f"search_{memory_type}_memory",
        namespace=namespace,
        instructions=search_instruction,
        store=store,
    )

    return [manage, search]


def long_term_memory_tools(
    namespace: tuple[str, ...] | str,
    store: Optional[BaseStore] = None,
) -> List[StructuredTool]:
    if isinstance(namespace, str):
        namespace = (namespace,)

    tools = (
        memory_tool(
            "actions",
            namespace=namespace + ("actions",),
            instruction=ACTION_INSTRUCTIONS,
            search_instruction=ACTION_SEARCH_INSTRUCTIONS,
            store=store,
        )
        + memory_tool(
            "failures",
            namespace=namespace + ("failures",),
            instruction=FAILURE_INSTRUCTIONS,
            search_instruction=FAILURE_SEARCH_INSTRUCTIONS,
            store=store,
        )
        + memory_tool(
            "decisions",
            namespace=namespace + ("decisions",),
            instruction=DECISION_INSTRUCTIONS,
            search_instruction=DECISION_SEARCH_INSTRUCTIONS,
            store=store,
        )
        + memory_tool(
            "insights",
            namespace=namespace + ("insights",),
            instruction=INSIGHT_INSTRUCTIONS,
            search_instruction=INSIGHT_SEARCH_INSTRUCTIONS,
            store=store,
        )
    )

    return tools

