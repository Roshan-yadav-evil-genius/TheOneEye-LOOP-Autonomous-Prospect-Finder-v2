import json
import os
from typing import Any

from langchain_core.messages import RemoveMessage, message_to_dict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from deepagents import create_deep_agent

from agents.model_provider import resolve_chat_model
from contracts.domain import ChatHistoryRead, StateSnapshotRead
from core.config import get_settings

from langchain_core.language_models import FakeListChatModel

def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _clean_value(val: Any) -> Any:
    if val is None or isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, (list, tuple, set)):
        return [_clean_value(item) for item in val]
    if isinstance(val, dict):
        return {str(k): _clean_value(v) for k, v in val.items()}
    if hasattr(val, "type") and hasattr(val, "content"):
        try:
            return message_to_dict(val)
        except Exception:
            pass
    if hasattr(val, "model_dump"):
        try:
            return _clean_value(val.model_dump(mode="json"))
        except Exception:
            pass
    if hasattr(val, "dict") and callable(getattr(val, "dict")):
        try:
            return _clean_value(val.dict())
        except Exception:
            pass
    if hasattr(val, "__dict__"):
        try:
            return {str(k): _clean_value(v) for k, v in val.__dict__.items() if not k.startswith("_")}
        except Exception:
            pass
    return str(val)


class ThreadChatHistoryService:
    @staticmethod
    async def get_history(thread_id: str, checkpoint_ns: str | None = None) -> ChatHistoryRead:
        conn_string = get_settings().resolved_threads_database_url
        if not conn_string:
            return ChatHistoryRead(thread_id=thread_id, messages=[], can_resume=False)

        try:
            async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
                if checkpoint_ns is not None:
                    config["configurable"]["checkpoint_ns"] = checkpoint_ns

                messages = []
                can_resume = False

                if checkpoint_ns:
                    tuple_val = await checkpointer.aget_tuple(config)
                    if tuple_val and tuple_val.checkpoint:
                        channel_values = tuple_val.checkpoint.get("channel_values", {})
                        raw_messages = (
                            channel_values.get("planner_chat")
                            or channel_values.get("evaluator_chat")
                            or channel_values.get("messages")
                            or []
                        )
                        for msg in raw_messages:
                            messages.append(message_to_dict(msg))
                        can_resume = bool(tuple_val.pending_writes)
                else:
                    try:
                        model = resolve_chat_model()
                    except Exception:
                        model = FakeListChatModel(responses=[""])

                    agent = create_deep_agent(model, checkpointer=checkpointer)
                    state = await agent.aget_state(config)
                    can_resume = bool(state.next) if state else False

                    if state and state.values:
                        raw_messages = state.values.get("planner_chat") or state.values.get("messages") or []
                        for msg in raw_messages:
                            messages.append(message_to_dict(msg))

                return ChatHistoryRead(thread_id=thread_id, messages=messages, can_resume=can_resume)
        except Exception:
            return ChatHistoryRead(thread_id=thread_id, messages=[], can_resume=False)

    @staticmethod
    async def get_state_history(
        thread_id: str, checkpoint_ns: str | None = None
    ) -> list[StateSnapshotRead]:
        conn_string = get_settings().resolved_threads_database_url
        if not conn_string:
            return []

        snapshots: list[StateSnapshotRead] = []
        try:
            async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
                if checkpoint_ns is not None:
                    config["configurable"]["checkpoint_ns"] = checkpoint_ns

                raw_tuples = []
                async for tuple_val in checkpointer.alist(config):
                    raw_tuples.append(tuple_val)

                raw_tuples.reverse()

                for idx, tuple_val in enumerate(raw_tuples, start=1):
                    cp = tuple_val.checkpoint or {}
                    meta = tuple_val.metadata or {}
                    cfg = tuple_val.config or {}
                    parent_cfg = tuple_val.parent_config or {}

                    configurable = cfg.get("configurable", {})
                    parent_configurable = parent_cfg.get("configurable", {})

                    cp_id = configurable.get("checkpoint_id")
                    cp_ns = configurable.get("checkpoint_ns")
                    parent_cp_id = parent_configurable.get("checkpoint_id")

                    channel_values = cp.get("channel_values", {})
                    clean_values = {str(k): _clean_value(v) for k, v in channel_values.items()}

                    next_raw = list(tuple_val.next) if hasattr(tuple_val, "next") and tuple_val.next else []
                    next_nodes = [item if isinstance(item, str) else str(item) for item in next_raw]

                    clean_metadata = _clean_value(meta)
                    if not isinstance(clean_metadata, dict):
                        clean_metadata = {}

                    snapshots.append(
                        StateSnapshotRead(
                            step_index=idx,
                            checkpoint_id=cp_id,
                            checkpoint_ns=cp_ns,
                            parent_checkpoint_id=parent_cp_id,
                            values=clean_values,
                            next=next_nodes,
                            metadata=clean_metadata,
                        )
                    )
            return snapshots
        except Exception as exc:
            import logging
            logging.error(f"Error fetching state history for thread {thread_id}: {exc}", exc_info=True)
            return []



    @staticmethod
    async def list_namespaces(thread_id: str) -> list[str]:
        from agents.checkpoints import ThreadCheckpointStore
        store = ThreadCheckpointStore()
        return await store.list_namespaces(thread_id)

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
            if not state or not state.values:
                return False

            chat_key = "planner_chat" if "planner_chat" in state.values else "messages"
            raw_messages = state.values.get(chat_key, [])
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
                await agent.aupdate_state(config, {chat_key: messages_to_remove})
            except Exception:
                nodes = [n for n in agent.get_graph().nodes.keys() if n not in ("__start__", "__end__")]
                node_name = "model" if "model" in agent.get_graph().nodes else (nodes[0] if nodes else None)
                if node_name:
                    await agent.aupdate_state(config, {chat_key: messages_to_remove}, as_node=node_name)
                else:
                    raise
            return True
        except Exception:
            return False

