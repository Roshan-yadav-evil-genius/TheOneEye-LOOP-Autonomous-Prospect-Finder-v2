"""LangMem tool factory for Brain Agent long-term memory."""

from typing import List

from langchain_core.tools import StructuredTool
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
):
    manage = create_manage_memory_tool(
        name=f"manage_{memory_type}_memory",
        namespace=namespace,
        instructions=instruction,
    )

    search = create_search_memory_tool(
        name=f"search_{memory_type}_memory",
        namespace=namespace,
        instructions=search_instruction,
    )

    return [manage, search]


def long_term_memory_tools(namespace: tuple[str, ...] | str) -> List[StructuredTool]:
    if isinstance(namespace, str):
        namespace = (namespace,)

    tools = (
        memory_tool(
            "actions",
            namespace=namespace + ("actions",),
            instruction=ACTION_INSTRUCTIONS,
            search_instruction=ACTION_SEARCH_INSTRUCTIONS,
        )
        + memory_tool(
            "failures",
            namespace=namespace + ("failures",),
            instruction=FAILURE_INSTRUCTIONS,
            search_instruction=FAILURE_SEARCH_INSTRUCTIONS,
        )
        + memory_tool(
            "decisions",
            namespace=namespace + ("decisions",),
            instruction=DECISION_INSTRUCTIONS,
            search_instruction=DECISION_SEARCH_INSTRUCTIONS,
        )
        + memory_tool(
            "insights",
            namespace=namespace + ("insights",),
            instruction=INSIGHT_INSTRUCTIONS,
            search_instruction=INSIGHT_SEARCH_INSTRUCTIONS,
        )
    )

    return tools
