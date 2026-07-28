from typing import Any

from langchain.agents.factory import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langgraph.graph.state import CompiledStateGraph

from agents.model_provider import resolve_chat_model
from agents.setup_chat.org_tools import get_all_tools as get_org_tools
from agents.setup_chat.product_tools import get_product_tools
from agents.setup_chat.strategy_tools import get_strategy_tools
from agents.setup_chat.prompts import render_setup_prompt


def create_strategy_setup_agent(checkpointer: Any) -> CompiledStateGraph:
    """Build the strategy setup chat agent."""
    system_prompt = render_setup_prompt(form_name="Strategy")
    
    # Org read only
    org_tools = [t for t in get_org_tools() if t.name == "get_organization_profile"]
    
    # Product read only
    product_tools = [t for t in get_product_tools() if t.name == "get_product_profile"]
    
    # Strategy read + write
    strategy_tools = get_strategy_tools()
    
    tools = org_tools + product_tools + strategy_tools
    model = resolve_chat_model()
    
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[TodoListMiddleware()],
        checkpointer=checkpointer,
    )
    
    return agent

