import json
import os
from typing import Any

from langchain_core.messages import RemoveMessage, message_to_dict
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

    @staticmethod
    async def delete_message(thread_id: str, message_id: str) -> bool:
        conn_string = get_settings().resolved_threads_database_url
        if conn_string:
            try:
                async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                    return await ThreadChatHistoryService._remove_message_from_checkpointer(
                        checkpointer, thread_id, message_id
                    )
            except Exception:
                return False
        else:
            from agents.checkpoint_runtime import checkpoint_scope
            try:
                async with checkpoint_scope() as checkpointer:
                    return await ThreadChatHistoryService._remove_message_from_checkpointer(
                        checkpointer, thread_id, message_id
                    )
            except Exception:
                return False

    @staticmethod
    async def _remove_message_from_checkpointer(
        checkpointer: Any, thread_id: str, message_id: str
    ) -> bool:
        try:
            try:
                model = resolve_chat_model()
            except Exception:
                model = FakeListChatModel(responses=[""])

            agent = create_deep_agent(model, checkpointer=checkpointer)
            config = _thread_config(thread_id)

            state = await agent.aget_state(config)
            if not state or not state.values or "messages" not in state.values:
                return False

            raw_messages = state.values["messages"]
            messages_to_remove = [RemoveMessage(id=message_id)]

            target_msg = None
            for m in raw_messages:
                if getattr(m, "id", None) == message_id:
                    target_msg = m
                    break

            if target_msg and hasattr(target_msg, "tool_calls") and target_msg.tool_calls:
                tool_call_ids = {
                    tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    for tc in target_msg.tool_calls
                }
                tool_call_ids.discard(None)
                if tool_call_ids:
                    for m in raw_messages:
                        if getattr(m, "tool_call_id", None) in tool_call_ids and getattr(m, "id", None):
                            messages_to_remove.append(RemoveMessage(id=m.id))

            try:
                await agent.aupdate_state(config, {"messages": messages_to_remove})
            except Exception:
                nodes = [n for n in agent.get_graph().nodes.keys() if n not in ("__start__", "__end__")]
                node_name = "model" if "model" in agent.get_graph().nodes else (nodes[0] if nodes else None)
                if node_name:
                    await agent.aupdate_state(config, {"messages": messages_to_remove}, as_node=node_name)
                else:
                    raise
            return True
        except Exception:
            return False

