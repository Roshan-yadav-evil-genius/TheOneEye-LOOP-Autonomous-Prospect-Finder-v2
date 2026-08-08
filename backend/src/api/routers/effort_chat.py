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
from agents.planner_graph import stream_planner_graph
from application.chat_history_service import ThreadChatHistoryService
from application.planner_service import PlannerService
from contracts.domain import ChatHistoryRead, ChatStreamRequest, NewThreadResponse, StateSnapshotRead
from core.config import get_settings
from persistence import models
from persistence.database import SessionFactory, get_session

router = APIRouter(prefix="/api/v1/efforts", tags=["effort-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]

# ... (omitted middle for concise replacement)



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


@router.get("/{effort_prefix}/chat/threads")
async def get_threads(
    effort_prefix: str,
) -> dict[str, Any]:
    base_thread_id = f"{effort_prefix}_planner_1"
    stem = f"{effort_prefix}_planner"
    store = ThreadCheckpointStore()
    found = await store.search_threads(prefix=stem)
    if not found:
        threads = [base_thread_id]
    else:
        cleaned = []
        for tid in found:
            if tid == stem:
                cleaned.append(base_thread_id)
            else:
                cleaned.append(tid)
        threads = list(dict.fromkeys(cleaned))

    namespaces_map: dict[str, list[str]] = {}
    for tid in threads:
        ns_list = await store.list_namespaces(tid)
        namespaces_map[tid] = ns_list

    return {
        "threads": threads,
        "namespaces": namespaces_map,
    }


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
                            chat_key = "planner_chat" if is_planner else "messages"
                            last_msg = data.message
                            await ThreadChatHistoryService.delete_message(thread_id, last_msg)

                input_data: Any = None if data.retry and can_resume else ({
                    "planner_chat": [data.message]
                } if is_planner and data.message else ([{"role": "user", "content": data.message}] if data.message else {}))

                try:
                    events = stream_planner_graph(graph, input_data, thread_id) if is_planner else graph.astream_events(input_data, config=config, version="v2")
                    disconnected = False
                    async for event in events:
                        if await request.is_disconnected():
                            disconnected = True
                            break
                        kind = event.get("event")
                        evt_data = event.get("data", {})
                        if kind == "on_chat_model_stream":
                            chunk = evt_data.get("chunk")
                            if chunk:
                                content = getattr(chunk, "content", "")
                                if isinstance(content, str) and content:
                                    yield f"event: message\ndata: {json.dumps({'content': content})}\n\n"

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
    checkpoint_ns: str | None = None,
) -> ChatHistoryRead:
    target_thread_id = thread_id or f"{effort_prefix}_planner_1"
    return await ThreadChatHistoryService.get_history(target_thread_id, checkpoint_ns=checkpoint_ns)


@router.get("/{effort_prefix}/chat/state-history", response_model=list[StateSnapshotRead])
async def get_state_history(
    effort_prefix: str,
    thread_id: str | None = None,
    checkpoint_ns: str | None = None,
) -> list[StateSnapshotRead]:
    target_thread_id = thread_id or f"{effort_prefix}_planner_1"
    return await ThreadChatHistoryService.get_state_history(target_thread_id, checkpoint_ns=checkpoint_ns)


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
    await ThreadChatHistoryService.delete_message(target_thread_id, message_id)


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

