from pathlib import Path
from typing import Any

from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledStateGraph

from agents.model_provider import resolve_chat_model
from agents.setup_chat.org_tools import get_all_tools as get_org_tools
from agents.setup_chat.product_tools import get_product_tools
from agents.setup_chat.strategy_tools import get_strategy_tools


def create_strategy_setup_agent(checkpointer: Any) -> CompiledStateGraph:
    """Build the strategy setup chat agent."""
    prompt_path = Path(__file__).parent / "prompts" / "strategy_setup_assistant.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    # Org read only
    org_tools = [t for t in get_org_tools() if t.name == "get_organization_profile"]
    
    # Product read only
    product_tools = [t for t in get_product_tools() if t.name == "get_product_profile"]
    
    # Strategy read + write
    strategy_tools = get_strategy_tools()
    
    tools = org_tools + product_tools + strategy_tools
    model = resolve_chat_model()
    
    agent = create_react_agent(
        model,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )
    
    return agent
