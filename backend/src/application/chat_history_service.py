import json
import os
from typing import Any

from langchain_core.messages import message_to_dict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from deepagents import create_deep_agent

from agents.model_provider import resolve_chat_model
from contracts.domain import ChatHistoryRead, ChatHistoryMessage
from core.config import get_settings


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


class ThreadChatHistoryService:
    @staticmethod
    async def get_history(thread_id: str) -> ChatHistoryRead:
        conn_string = get_settings().resolved_threads_database_url
        if not conn_string:
            return ChatHistoryRead(thread_id=thread_id, messages=[], can_resume=False)

        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            model = resolve_chat_model()
            agent = create_deep_agent(model, checkpointer=checkpointer)
            state = await agent.aget_state(_thread_config(thread_id))
            can_resume = bool(state.next) if state else False
            messages = []
            
            if state and state.values and "messages" in state.values:
                raw_messages = state.values["messages"]
                for msg in raw_messages:
                    msg_dict = message_to_dict(msg)
                    with open("master.json",'w') as file:
                        file.write(json.dumps(msg_dict))
                    msg_type = msg_dict.get("type")
                    data = msg_dict.get("data", {})
                    
                    if msg_type == "human":
                        content = data.get("content", "")
                        messages.append(
                            ChatHistoryMessage(
                                role="user",
                                content=content if isinstance(content, str) else json.dumps(content)
                            )
                        )
                    elif msg_type == "ai":
                        content = data.get("content", "")
                        tool_calls = data.get("tool_calls", [])
                        kwargs = data.get("additional_kwargs", {})
                        
                        # Extract reasoning
                        reasoning = kwargs.get("reasoning_content") or kwargs.get("reasoning")
                        if not reasoning and isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "reasoning":
                                    reasoning = block.get("text", "")
                                    break
                                
                        if reasoning:
                            messages.append(
                                ChatHistoryMessage(
                                    role="reasoning",
                                    content=str(reasoning)
                                )
                            )

                        content_str = content if isinstance(content, str) else json.dumps(content)
                        
                        if content and content_str not in ('""', '"[]"', "[]"):
                            messages.append(
                                ChatHistoryMessage(
                                    role="assistant",
                                    content=content_str
                                )
                            )
                        for tc in tool_calls:
                            messages.append(
                                ChatHistoryMessage(
                                    role="tool_call",
                                    content="",
                                    name=tc.get("name"),
                                    args=tc.get("args")
                                )
                            )
                    elif msg_type == "tool":
                        content = data.get("content", "")
                        content_str = content if isinstance(content, str) else json.dumps(content)
                        messages.append(
                            ChatHistoryMessage(
                                role="tool_result",
                                content=content_str,
                                name=data.get("name")
                            )
                        )

            return ChatHistoryRead(thread_id=thread_id, messages=messages, can_resume=can_resume)
