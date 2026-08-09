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
                        try:
                            store = ThreadCheckpointStore()
                            ns_list = await store.list_namespaces(thread_id)
                            for ns in ns_list:
                                if not ns:
                                    continue
                                ns_st = await graph.aget_state({"configurable": {"thread_id": thread_id, "checkpoint_ns": ns}})
                                if ns_st and bool(getattr(ns_st, "next", None)):
                                    can_resume = True
                                    break
                        except Exception:
                            pass

                    if not can_resume:
                        if data.redo_last and data.message:
                            chat_key = "planner_chat" if is_planner else "messages"
                            last_msg = data.message
                            await ThreadChatHistoryService.delete_message(thread_id, last_msg)

                input_data: Any = None if (data.retry and can_resume) else ({
                    "planner_chat": [data.message]
                } if is_planner and data.message else ([{"role": "user", "content": data.message}] if data.message else {}))

                try:
                    events = stream_planner_graph(graph, input_data, thread_id) if is_planner else graph.astream_events(input_data, config=config, version="v2", subgraphs=True)
                    disconnected = False
                    emitted_tool_call_ids: set[str] = set()
                    emitted_tool_result_ids: set[str] = set()
                    tool_name_map: dict[str, str] = {}

                    async for event in events:
                        if await request.is_disconnected():
                            disconnected = True
                            break
                        kind = event.get("event")
                        evt_data = event.get("data", {})

                        if kind == "on_chat_model_stream":
                            chunk = evt_data.get("chunk")
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
                            output = evt_data.get("output", {})
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
                            name = event.get("name")
                            if name and not name.startswith("_"):
                                tool_id = event.get("run_id")
                                if tool_id:
                                    tool_name_map[tool_id] = name
                                    if tool_id not in emitted_tool_call_ids:
                                        emitted_tool_call_ids.add(tool_id)
                                        args = evt_data.get("input", {})
                                        yield f"event: tool_call\ndata: {json.dumps({'id': tool_id, 'name': name, 'args': args})}\n\n"

                        elif kind == "on_tool_end":
                            name = event.get("name")
                            if name and not name.startswith("_"):
                                tool_id = event.get("run_id")
                                if tool_id and tool_id not in emitted_tool_result_ids:
                                    emitted_tool_result_ids.add(tool_id)
                                    output = evt_data.get("output", "")
                                    if hasattr(output, "content"):
                                        output = output.content

                                    if not isinstance(output, str):
                                        try:
                                            output = json.dumps(output)
                                        except Exception:
                                            output = str(output)
                                    t_name = name or tool_name_map.get(tool_id, "tool")
                                    yield f"event: tool_result\ndata: {json.dumps({'id': t_name and t_name != 'tool' and tool_id or tool_id, 'name': t_name, 'content': output})}\n\n"

                        elif kind == "on_chain_end" and event.get("name") == "tools":
                            output_dict = evt_data.get("output", {})
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

