from pathlib import Path
from typing import Any

from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledStateGraph

from agents.model_provider import resolve_chat_model
from agents.organization_setup.tools import get_all_tools


def create_organization_setup_agent(checkpointer: Any) -> CompiledStateGraph:
    """Build the organization setup chat agent."""
    prompt_path = Path(__file__).parent / "prompts" / "organization_setup_assistant.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    tools = get_all_tools()
    model = resolve_chat_model()
    
    agent = create_react_agent(
        model,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )
    
    return agent
