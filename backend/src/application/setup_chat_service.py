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
        from application.chat_history_service import ThreadChatHistoryService
        await ThreadChatHistoryService.delete_thread(self.thread_id)

    async def delete_message(self, message_id: str) -> bool:
        from application.chat_history_service import ThreadChatHistoryService
        return await ThreadChatHistoryService.delete_message(self.thread_id, message_id)

    async def stream_chat(
        self, 
        request: ChatStreamRequest, 
        fastapi_request=None
    ) -> AsyncGenerator[str, None]:
        config = {
            "recursion_limit": get_settings().agent_recursion_limit,
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
                emitted_tool_call_ids: set[str] = set()
                emitted_tool_result_ids: set[str] = set()
                tool_name_map: dict[str, str] = {}

                async for event in agent.astream_events(
                    input_data,
                    config,
                    version="v2",
                    subgraphs=True
                ):

                    if fastapi_request and await fastapi_request.is_disconnected():
                        disconnected = True
                        break

                    kind = event["event"]
                    data = event.get("data", {})
                    
                    if kind == "on_chat_model_stream":
                        chunk = data.get("chunk")
                        if chunk:
                            reasoning = None
                            if hasattr(chunk, "additional_kwargs") and chunk.additional_kwargs:
                                reasoning = (
                                    chunk.additional_kwargs.get("reasoning_content")
                                    or chunk.additional_kwargs.get("reasoning")
                                    or chunk.additional_kwargs.get("thinking")
                                    or chunk.additional_kwargs.get("thought")
                                )
                            if not reasoning:
                                reasoning = (
                                    getattr(chunk, "reasoning_content", None)
                                    or getattr(chunk, "thinking", None)
                                )
                            if not reasoning and isinstance(getattr(chunk, "content", None), list):
                                for block in chunk.content:
                                    if isinstance(block, dict) and block.get("type") in ("reasoning", "thinking"):
                                        reasoning = block.get("reasoning") or block.get("thinking") or block.get("text")
                                        if reasoning:
                                            break

                            if reasoning:
                                yield f"event: reasoning\ndata: {json.dumps({'text': reasoning})}\n\n"

                            content = getattr(chunk, "content", "")
                            if content:
                                if isinstance(content, list):
                                    text_parts = []
                                    for block in content:
                                        if isinstance(block, str):
                                            text_parts.append(block)
                                        elif isinstance(block, dict) and block.get("type") in ("text", "content"):
                                            text_parts.append(block.get("text") or block.get("content") or "")
                                    content = "".join(text_parts)

                                if isinstance(content, str) and content:
                                    yield f"event: content\ndata: {json.dumps({'text': content})}\n\n"

                                
                    elif kind == "on_chat_model_end":
                        # Extracted message can either be wrapped in an LLMResult (generations)
                        # or emitted directly as an AIMessage/AIMessageChunk in astream_events v2.
                        output = data.get("output", {})
                        msg = None
                        if hasattr(output, "generations") and len(output.generations) > 0 and len(output.generations[0]) > 0:
                            msg = getattr(output.generations[0][0], "message", None)
                        elif hasattr(output, "content") or hasattr(output, "tool_calls"):
                            msg = output

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
                            
                            # Stream requested tool calls live as soon as the model finishes generating them.
                            # This ensures the frontend renders the tool call card immediately even if ModeMiddleware
                            # short-circuits the tool node before execution.
                            tool_calls = getattr(msg, "tool_calls", None)
                            if tool_calls and isinstance(tool_calls, list):
                                for tc in tool_calls:
                                    if isinstance(tc, dict):
                                        tc_id = tc.get("id")
                                        tc_name = tc.get("name")
                                        tc_args = tc.get("args", {})
                                        if tc_id and tc_name:
                                            tool_name_map[tc_id] = tc_name
                                            if tc_id not in emitted_tool_call_ids:
                                                emitted_tool_call_ids.add(tc_id)
                                                yield f"event: tool_call\ndata: {json.dumps({'id': tc_id, 'name': tc_name, 'args': tc_args})}\n\n"
                                
                    elif kind == "on_tool_start":
                        # Backup handler for tool calls if not already emitted by on_chat_model_end
                        name = event.get("name")
                        tool_id = event.get("run_id")
                        if tool_id and name:
                            tool_name_map[tool_id] = name
                            if tool_id not in emitted_tool_call_ids:
                                emitted_tool_call_ids.add(tool_id)
                                args = data.get("input", {})
                                yield f"event: tool_call\ndata: {json.dumps({'id': tool_id, 'name': name, 'args': args})}\n\n"
                            
                    elif kind == "on_tool_end":
                        # Standard tool execution result stream
                        name = event.get("name")
                        tool_id = event.get("run_id")
                        if tool_id and tool_id not in emitted_tool_result_ids:
                            emitted_tool_result_ids.add(tool_id)
                            output = data.get("output", "")
                            if hasattr(output, "content"):
                                output = output.content
                                
                            if not isinstance(output, str):
                                try:
                                    output = json.dumps(output)
                                except Exception:
                                    output = str(output)
                            t_name = name or tool_name_map.get(tool_id, "tool")
                            yield f"event: tool_result\ndata: {json.dumps({'id': tool_id, 'name': t_name, 'content': output})}\n\n"

                    elif kind == "on_chain_end" and event.get("name") == "tools":
                        # When ModeMiddleware blocks a tool (e.g. state modification tool in ASK mode),
                        # it short-circuits execution and returns a ToolMessage directly.
                        # Since the tool function itself is skipped, on_tool_end won't fire.
                        # We intercept the ToolMessages returned by the 'tools' node here to stream the result live.
                        output_dict = data.get("output", {})
                        msgs = output_dict.get("messages", []) if isinstance(output_dict, dict) else []
                        for msg in msgs:
                            tool_id = getattr(msg, "tool_call_id", None)
                            if tool_id and tool_id not in emitted_tool_result_ids:
                                emitted_tool_result_ids.add(tool_id)
                                content = getattr(msg, "content", "")
                                if not isinstance(content, str):
                                    try:
                                        content = json.dumps(content)
                                    except Exception:
                                        content = str(content)
                                t_name = getattr(msg, "name", None) or tool_name_map.get(tool_id, "tool")
                                yield f"event: tool_result\ndata: {json.dumps({'id': tool_id, 'name': t_name, 'content': content})}\n\n"

                if disconnected:
                    state = await agent.aget_state(config)
                    yield f"event: incomplete\ndata: {json.dumps({'can_resume': bool(state.next)})}\n\n"
                else:
                    yield f"event: done\ndata: {json.dumps({'thread_id': self.thread_id})}\n\n"
                
            except Exception as e:
                state = await agent.aget_state(config)
                yield f"event: error\ndata: {json.dumps({'message': str(e), 'can_resume': bool(state.next)})}\n\n"
