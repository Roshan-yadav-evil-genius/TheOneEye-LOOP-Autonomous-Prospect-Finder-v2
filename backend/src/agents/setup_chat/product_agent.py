from typing import Any

from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledStateGraph

from agents.model_provider import resolve_chat_model
from agents.setup_chat.org_tools import get_all_tools as get_org_tools
from agents.setup_chat.product_tools import get_product_tools
from agents.setup_chat.prompts import render_setup_prompt


def create_product_setup_agent(checkpointer: Any) -> CompiledStateGraph:
    """Build the product setup chat agent."""
    system_prompt = render_setup_prompt(form_name="Product/service")
    
    # Org read only
    org_tools = [t for t in get_org_tools() if t.name == "get_organization_profile"]
    product_tools = get_product_tools()
    
    tools = org_tools + product_tools
    model = resolve_chat_model()
    
    agent = create_react_agent(
        model,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )
    
    return agent
