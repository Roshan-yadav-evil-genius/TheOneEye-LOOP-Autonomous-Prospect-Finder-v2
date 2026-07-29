import json
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from langchain_core.messages import message_to_dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from agents.checkpoints import ThreadCheckpointStore
from agents.checkpoint_runtime import checkpoint_scope
from agents.factory import (
    company_finder_agent_scope,
    contact_finder_agent_scope,
)
from contracts.domain import ChatHistoryRead, ChatStreamRequest, NewThreadResponse
from core.config import get_settings
from persistence import models
from persistence.database import SessionFactory, get_session

router = APIRouter(prefix="/api/v1/efforts", tags=["effort-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]


async def get_effort_info(session: AsyncSession, effort_prefix: str) -> tuple[str, str, str | None]:
    """Retrieve strategy_id, role, and company_id for an effort_prefix."""
    run = await session.scalar(
        select(models.AgentRun).where(models.AgentRun.effort_prefix == effort_prefix)
    )
    if run:
        return run.sales_strategy_id, run.agent_role, run.company_id

    # Fallback to parsing effort_prefix:
    # Company effort prefix: LOOP_{org_id}_{product_id}_{strategy_id}_{effort_seq}
    # Contact effort prefix: LOOP_{org_id}_{product_id}_{strategy_id}_{attempt}_{company_id}_{seq}
    parts = effort_prefix.split("_")
    if len(parts) >= 5 and parts[0] == "LOOP":
        strategy_id = parts[3]
        if len(parts) >= 7:
            company_id = parts[5]
            return strategy_id, "contact_finder", company_id
        return strategy_id, "company_finder", None

    raise ValueError(f"Could not determine strategy and role for effort_prefix: {effort_prefix}")


@router.get("/{effort_prefix}/chat/threads", response_model=list[str])
async def get_threads(
    effort_prefix: str,
) -> list[str]:
    planner_thread_id = f"{effort_prefix}_planner"
    store = ThreadCheckpointStore()
    found = await store.search_threads(prefix=planner_thread_id)
    if not found:
        return [planner_thread_id]
    return found


@router.post("/{effort_prefix}/chat/new-thread", response_model=NewThreadResponse)
async def new_thread(
    effort_prefix: str,
) -> NewThreadResponse:
    planner_thread_id = f"{effort_prefix}_planner"
    return NewThreadResponse(thread_id=planner_thread_id)


@router.post("/{effort_prefix}/chat/stream")
async def stream_chat(
    effort_prefix: str,
    data: ChatStreamRequest,
    request: Request,
) -> StreamingResponse:
    async def _stream_with_session():
        async with SessionFactory() as session:
            strategy_id, role, company_id = await get_effort_info(session, effort_prefix)
            thread_id = data.thread_id or f"{effort_prefix}_planner"

            if role in ("company_finder", "company-finder"):
                scope_cm = company_finder_agent_scope(session, strategy_id, effort_prefix)
            else:
                scope_cm = contact_finder_agent_scope(
                    session, strategy_id, company_id or "", effort_prefix
                )

            async with scope_cm as (graph, scope_config, parent_store):
                config = {
                    "recursion_limit": 100,
                    "configurable": {
                        "thread_id": thread_id,
                    },
                }

                if data.retry:
                    try:
                        state = await graph.aget_state(config)
                        can_resume = bool(getattr(state, "next", None))
                    except Exception:
                        can_resume = False
                    if not can_resume:
                        if data.redo_last and data.message:
                            input_data = {"messages": [("user", data.message)]}
                        else:
                            yield f"event: error\ndata: {json.dumps({'message': 'No pending actions to retry.', 'can_resume': False})}\n\n"
                            return
                    else:
                        input_data = None
                else:
                    input_data = {"messages": [("user", data.message)]}

                disconnected = False
                try:
                    async for event in graph.astream_events(input_data, config, version="v2"):
                        if await request.is_disconnected():
                            disconnected = True
                            break

                        kind = event["event"]
                        evt_data = event.get("data", {})

                        if kind == "on_chat_model_stream":
                            chunk = evt_data.get("chunk")
                            if chunk:
                                if (
                                    hasattr(chunk, "additional_kwargs")
                                    and "reasoning_content" in chunk.additional_kwargs
                                ):
                                    reasoning = chunk.additional_kwargs["reasoning_content"]
                                    if reasoning:
                                        yield f"event: reasoning\ndata: {json.dumps({'text': reasoning})}\n\n"

                                content = chunk.content
                                if content:
                                    if isinstance(content, list):
                                        content = json.dumps(content)
                                    yield f"event: content\ndata: {json.dumps({'text': content})}\n\n"

                        elif kind == "on_chat_model_end":
                            output = evt_data.get("output", {})
                            if (
                                hasattr(output, "generations")
                                and len(output.generations) > 0
                                and len(output.generations[0]) > 0
                            ):
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
                            if name and not name.startswith("_"):
                                tool_id = event.get("run_id")
                                args = evt_data.get("input", {})
                                yield f"event: tool_call\ndata: {json.dumps({'id': tool_id, 'name': name, 'args': args})}\n\n"

                        elif kind == "on_tool_end":
                            name = event.get("name")
                            if name and not name.startswith("_"):
                                tool_id = event.get("run_id")
                                output = evt_data.get("output", "")
                                if hasattr(output, "content"):
                                    output = output.content

                                if not isinstance(output, str):
                                    try:
                                        output = json.dumps(output)
                                    except Exception:
                                        output = str(output)
                                yield f"event: tool_result\ndata: {json.dumps({'id': tool_id, 'name': name, 'content': output})}\n\n"

                    if disconnected:
                        yield f"event: incomplete\ndata: {json.dumps({'can_resume': False})}\n\n"
                    else:
                        yield f"event: done\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
                except Exception as e:
                    yield f"event: error\ndata: {json.dumps({'message': str(e), 'can_resume': False})}\n\n"

    return StreamingResponse(
        _stream_with_session(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/{effort_prefix}/chat/history", response_model=ChatHistoryRead)
async def get_history(
    effort_prefix: str,
    thread_id: str | None = None,
) -> ChatHistoryRead:
    target_thread_id = thread_id or f"{effort_prefix}_planner"
    async with checkpoint_scope() as checkpointer:
        config = {"configurable": {"thread_id": target_thread_id}}

        if hasattr(checkpointer, "aget"):
            checkpoint = await checkpointer.aget(config)
        else:
            checkpoint = checkpointer.get(config)

        messages = []
        if (
            checkpoint
            and "channel_values" in checkpoint
            and "messages" in checkpoint["channel_values"]
        ):
            raw_messages = checkpoint["channel_values"]["messages"]
            for msg in raw_messages:
                messages.append(message_to_dict(msg))

        return ChatHistoryRead(thread_id=target_thread_id, messages=messages, can_resume=False)


@router.delete("/{effort_prefix}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    effort_prefix: str,
    thread_id: str | None = None,
) -> None:
    target_thread_id = thread_id or f"{effort_prefix}_planner"
    settings = get_settings()
    if settings.threads_enabled and settings.threads_database_url:
        from psycopg_pool import AsyncConnectionPool

        async with AsyncConnectionPool(
            settings.threads_database_url, open=False, kwargs={"autocommit": True}
        ) as pool:
            await pool.open()
            async with pool.connection() as conn:
                await conn.execute(
                    "DELETE FROM checkpoints WHERE thread_id = %s", (target_thread_id,)
                )
                await conn.execute(
                    "DELETE FROM checkpoint_writes WHERE thread_id = %s", (target_thread_id,)
                )
    else:
        async with checkpoint_scope() as checkpointer:
            if hasattr(checkpointer, "storage"):
                keys_to_delete = [
                    k for k in checkpointer.storage.keys() if k[0] == target_thread_id
                ]
                for k in keys_to_delete:
                    del checkpointer.storage[k]
