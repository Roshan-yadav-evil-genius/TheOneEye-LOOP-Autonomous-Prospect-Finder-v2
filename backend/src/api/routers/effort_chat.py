import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from agents.checkpoints import ThreadCheckpointStore
from agents.factory import (
    company_finder_agent_scope,
    contact_finder_agent_scope,
)
from agents.runtime import allocate_next_setup_thread_id
from application.chat_history_service import ThreadChatHistoryService
from application.planner_service import PlannerService
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
    base_thread_id = f"{effort_prefix}_planner_1"
    stem = f"{effort_prefix}_planner"
    store = ThreadCheckpointStore()
    found = await store.search_threads(prefix=stem)
    if not found:
        return [base_thread_id]
    cleaned = []
    for tid in found:
        if tid == stem:
            cleaned.append(base_thread_id)
        else:
            cleaned.append(tid)
    return list(dict.fromkeys(cleaned))


@router.post("/{effort_prefix}/chat/new-thread", response_model=NewThreadResponse)
async def new_thread(
    effort_prefix: str,
) -> NewThreadResponse:
    base_thread_id = f"{effort_prefix}_planner_1"
    stem = f"{effort_prefix}_planner"
    store = ThreadCheckpointStore()
    existing = await store.search_threads(prefix=stem)
    next_id = allocate_next_setup_thread_id(base_thread_id, existing)
    return NewThreadResponse(thread_id=next_id)


@router.post("/{effort_prefix}/chat/stream")
async def stream_chat(
    effort_prefix: str,
    data: ChatStreamRequest,
    request: Request,
) -> StreamingResponse:
    async def _stream_with_session():
        async with SessionFactory() as session:
            strategy_id, role, company_id = await get_effort_info(session, effort_prefix)
            thread_id = data.thread_id or f"{effort_prefix}_planner_1"
            is_planner = data.is_planner or "_planner" in thread_id

            if role in ("company_finder", "company-finder", "company_planner", "planner"):
                scope_cm = company_finder_agent_scope(
                    session,
                    strategy_id,
                    effort_prefix,
                    is_planner=is_planner,
                    role_suffix="planner" if is_planner else "company_finder",
                )
            else:
                scope_cm = contact_finder_agent_scope(
                    session, strategy_id, company_id or "", effort_prefix
                )

            async with scope_cm as (graph, scope_config, parent_store):
                config = {
                    "recursion_limit": get_settings().agent_recursion_limit,
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
    target_thread_id = thread_id or f"{effort_prefix}_planner_1"
    return await ThreadChatHistoryService.get_history(target_thread_id)


@router.delete("/{effort_prefix}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    effort_prefix: str,
    thread_id: str | None = None,
) -> None:
    target_thread_id = thread_id or f"{effort_prefix}_planner_1"
    await ThreadChatHistoryService.delete_thread(target_thread_id)


@router.delete("/{effort_prefix}/chat/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_message(
    effort_prefix: str,
    message_id: str,
    thread_id: str | None = None,
) -> None:
    target_thread_id = thread_id or f"{effort_prefix}_planner_1"
    success = await ThreadChatHistoryService.delete_message(target_thread_id, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message {message_id}",
        )


@router.get("/{effort_prefix}/plan")
async def get_effort_plan(
    effort_prefix: str,
    session: Session,
) -> dict[str, Any]:
    """Retrieve structured Planner domain state (plan_data) for an effort."""
    strategy_id = None
    try:
        strategy_id, _, _ = await get_effort_info(session, effort_prefix)
    except Exception:
        pass
    svc = PlannerService(session)
    plan = await svc.get_or_create_plan(effort_prefix, strategy_id=strategy_id)
    return plan.model_dump(mode="json")

