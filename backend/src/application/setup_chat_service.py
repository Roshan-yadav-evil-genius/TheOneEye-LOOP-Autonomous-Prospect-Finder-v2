import json
from collections.abc import AsyncGenerator, Callable, Awaitable
from typing import Any

from agents.checkpoint_runtime import checkpoint_scope
from contracts.domain import ChatStreamRequest, ChatHistoryRead
from core.config import get_settings
from langchain_core.messages import message_to_dict


class SetupChatService:
    def __init__(
        self,
        thread_id: str,
        verify_entity: Callable[[], Awaitable[None]],
        agent_factory: Callable[[Any], Any],
        tool_context: Any,
    ) -> None:
        self.thread_id = thread_id
        self.verify_entity = verify_entity
        self.agent_factory = agent_factory
        self.tool_context = tool_context

    async def get_history(self) -> ChatHistoryRead:
        async with checkpoint_scope() as checkpointer:
            config = {"configurable": {"thread_id": self.thread_id}}
            
            agent = self.agent_factory(checkpointer)
            state = await agent.aget_state(config)
            can_resume = bool(state.next)
            
            if hasattr(checkpointer, "aget"):
                checkpoint = await checkpointer.aget(config)
            else:
                checkpoint = checkpointer.get(config)
            
            messages = []
            if checkpoint and "channel_values" in checkpoint and "messages" in checkpoint["channel_values"]:
                raw_messages = checkpoint["channel_values"]["messages"]
                for msg in raw_messages:
                    messages.append(message_to_dict(msg))
                    
            return ChatHistoryRead(thread_id=self.thread_id, messages=messages, can_resume=can_resume)

    async def clear_chat(self) -> None:
        settings = get_settings()
        if settings.threads_enabled and settings.threads_database_url:
            from psycopg_pool import AsyncConnectionPool
            async with AsyncConnectionPool(settings.threads_database_url, open=False, kwargs={"autocommit": True}) as pool:
                await pool.open()
                async with pool.connection() as conn:
                    await conn.execute("DELETE FROM checkpoints WHERE thread_id = %s", (self.thread_id,))
                    await conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (self.thread_id,))
        else:
            # MemorySaver
            async with checkpoint_scope() as checkpointer:
                if hasattr(checkpointer, "storage"):
                    keys_to_delete = [k for k in checkpointer.storage.keys() if k[0] == self.thread_id]
                    for k in keys_to_delete:
                        del checkpointer.storage[k]

    async def stream_chat(
        self, 
        request: ChatStreamRequest, 
        fastapi_request=None
    ) -> AsyncGenerator[str, None]:
        config = {
            "configurable": {
                "thread_id": self.thread_id,
                "tool_context": self.tool_context
            }
        }
        
        async with checkpoint_scope() as checkpointer:
            agent = self.agent_factory(checkpointer)
            
            try:
                await self.verify_entity()
                
                if request.retry:
                    state = await agent.aget_state(config)
                    can_resume = bool(state.next)
                    if not can_resume:
                        if request.redo_last and request.message:
                            input_data = {"messages": [("user", request.message)]}
                        else:
                            yield f"event: error\ndata: {json.dumps({'message': 'No pending actions to retry.', 'can_resume': False})}\n\n"
                            return
                    else:
                        input_data = None
                else:
                    input_data = {"messages": [("user", request.message)]}
                
                disconnected = False
                async for event in agent.astream_events(
                    input_data,
                    config,
                    version="v2"
                ):
                    if fastapi_request and await fastapi_request.is_disconnected():
                        disconnected = True
                        break

                    kind = event["event"]
                    data = event.get("data", {})
                    
                    if kind == "on_chat_model_stream":
                        chunk = data.get("chunk")
                        if chunk:
                            if hasattr(chunk, "additional_kwargs") and "reasoning_content" in chunk.additional_kwargs:
                                reasoning = chunk.additional_kwargs["reasoning_content"]
                                if reasoning:
                                    yield f"event: reasoning\ndata: {json.dumps({'text': reasoning})}\n\n"
                            
                            content = chunk.content
                            if content:
                                if isinstance(content, list):
                                    content = json.dumps(content)
                                yield f"event: content\ndata: {json.dumps({'text': content})}\n\n"
                                
                    elif kind == "on_chat_model_end":
                        output = data.get("output", {})
                        # output can be an LLMResult with generations, let's extract the message
                        if hasattr(output, "generations") and len(output.generations) > 0 and len(output.generations[0]) > 0:
                            msg = getattr(output.generations[0][0], "message", None)
                            if msg:
                                meta = {}
                                if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                                    meta["usage_metadata"] = msg.usage_metadata
                                if hasattr(msg, "response_metadata") and msg.response_metadata:
                                    meta["response_metadata"] = msg.response_metadata
                                if hasattr(msg, "id") and msg.id:
                                    meta["id"] = msg.id
                                if meta:
                                    yield f"event: metadata\ndata: {json.dumps(meta)}\n\n"
                                
                    elif kind == "on_tool_start":
                        name = event.get("name")
                        if name and name.startswith(("get_", "set_")):
                            tool_id = event.get("run_id")
                            args = data.get("input", {})
                            yield f"event: tool_call\ndata: {json.dumps({'id': tool_id, 'name': name, 'args': args})}\n\n"
                            
                    elif kind == "on_tool_end":
                        name = event.get("name")
                        if name and name.startswith(("get_", "set_")):
                            tool_id = event.get("run_id")
                            output = data.get("output", "")
                            if hasattr(output, "content"):
                                output = output.content
                                
                            if not isinstance(output, str):
                                try:
                                    output = json.dumps(output)
                                except Exception:
                                    output = str(output)
                            yield f"event: tool_result\ndata: {json.dumps({'id': tool_id, 'name': name, 'content': output})}\n\n"

                if disconnected:
                    state = await agent.aget_state(config)
                    yield f"event: incomplete\ndata: {json.dumps({'can_resume': bool(state.next)})}\n\n"
                else:
                    yield f"event: done\ndata: {json.dumps({'thread_id': self.thread_id})}\n\n"
                
            except Exception as e:
                state = await agent.aget_state(config)
                yield f"event: error\ndata: {json.dumps({'message': str(e), 'can_resume': bool(state.next)})}\n\n"
