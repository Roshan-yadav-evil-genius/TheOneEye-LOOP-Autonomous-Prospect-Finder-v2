from typing import Any

from langchain.agents.factory import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langgraph.graph.state import CompiledStateGraph

from agents.model_provider import resolve_chat_model
from agents.setup_chat.org_tools import get_all_tools
from agents.setup_chat.prompts import render_setup_prompt


def create_organization_setup_agent(checkpointer: Any) -> CompiledStateGraph:
    """Build the organization setup chat agent."""
    system_prompt = render_setup_prompt(form_type="organization")
    
    tools = get_all_tools()
    model = resolve_chat_model()
    
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[TodoListMiddleware()],
        checkpointer=checkpointer,
    )
    
    return agent

