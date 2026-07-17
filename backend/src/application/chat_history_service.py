import json
import os
from typing import Any

from langchain_core.messages import message_to_dict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from deepagents import create_deep_agent

from agents.model_provider import resolve_chat_model
from contracts.domain import ChatHistoryRead
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
                    messages.append(msg_dict)
                    with open("master.json",'w') as file:
                        file.write(json.dumps(msg_dict)+"\n")

            return ChatHistoryRead(thread_id=thread_id, messages=messages, can_resume=can_resume)
