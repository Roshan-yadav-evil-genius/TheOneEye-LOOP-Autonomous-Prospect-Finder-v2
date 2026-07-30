import json
import os
from typing import Any

from langchain_core.messages import message_to_dict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from deepagents import create_deep_agent

from agents.model_provider import resolve_chat_model
from contracts.domain import ChatHistoryRead
from core.config import get_settings

from langchain_core.language_models import FakeListChatModel

def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


class ThreadChatHistoryService:
    @staticmethod
    async def get_history(thread_id: str) -> ChatHistoryRead:
        conn_string = get_settings().resolved_threads_database_url
        if not conn_string:
            return ChatHistoryRead(thread_id=thread_id, messages=[], can_resume=False)

        try:
            async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                try:
                    model = resolve_chat_model()
                except Exception:
                    model = FakeListChatModel(responses=[""])

                agent = create_deep_agent(model, checkpointer=checkpointer)
                state = await agent.aget_state(_thread_config(thread_id))
                can_resume = bool(state.next) if state else False
                messages = []

                if state and state.values and "messages" in state.values:
                    raw_messages = state.values["messages"]
                    for msg in raw_messages:
                        messages.append(message_to_dict(msg))

                return ChatHistoryRead(thread_id=thread_id, messages=messages, can_resume=can_resume)
        except Exception:
            return ChatHistoryRead(thread_id=thread_id, messages=[], can_resume=False)

    @staticmethod
    async def delete_thread(thread_id: str) -> bool:
        conn_string = get_settings().resolved_threads_database_url
        if conn_string:
            try:
                async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                    await checkpointer.adelete_thread(thread_id)
                return True
            except Exception:
                return False
        else:
            from agents.checkpoint_runtime import checkpoint_scope
            try:
                async with checkpoint_scope() as checkpointer:
                    if hasattr(checkpointer, "storage"):
                        keys_to_delete = [k for k in checkpointer.storage.keys() if k[0] == thread_id]
                        for k in keys_to_delete:
                            del checkpointer.storage[k]
                return True
            except Exception:
                return False

