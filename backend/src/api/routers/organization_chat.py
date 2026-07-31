import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from agents.runtime import build_org_setup_thread_id, allocate_next_setup_thread_id
from application.loop_service import LoopService
from application.setup_chat_service import SetupChatService
from agents.setup_chat.org_agent import create_organization_setup_agent
from agents.setup_chat.common import SetupChatToolContext
from contracts.domain import ChatStreamRequest, ChatHistoryRead, NewThreadResponse
from persistence.database import SessionFactory, get_session

from agents.checkpoints import ThreadCheckpointStore

router = APIRouter(prefix="/api/v1", tags=["organization-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]

def chat_service(
    session: AsyncSession,
    request: Request,
    organization_id: str,
    thread_id: str | None = None,
) -> SetupChatService:
    loop_service = LoopService(session, getattr(request.state, "request_id", None))
    
    async def verify_entity() -> None:
        await loop_service.get_organization(organization_id)
        
    actual_thread_id = thread_id or build_org_setup_thread_id(organization_id)
    tool_context = SetupChatToolContext(
        organization_id=organization_id,
        mode="chat", # Set appropriately in stream, but context is updated per stream request later
        service=loop_service,
    )
    
    return SetupChatService(
        thread_id=actual_thread_id,
        verify_entity=verify_entity,
        agent_factory=create_organization_setup_agent,
        tool_context=tool_context
    )


@router.get("/organizations/{organization_id}/chat/threads", response_model=list[str])
async def get_threads(organization_id: str) -> list[str]:
    store = ThreadCheckpointStore()
    base = build_org_setup_thread_id(organization_id)
    stem = re.sub(r"_\d+$", "", base)
    return await store.search_threads(prefix=stem)


@router.post("/organizations/{organization_id}/chat/new-thread", response_model=NewThreadResponse)
async def new_thread(organization_id: str) -> NewThreadResponse:
    store = ThreadCheckpointStore()
    base = build_org_setup_thread_id(organization_id)
    stem = re.sub(r"_\d+$", "", base)
    existing = await store.search_threads(prefix=stem)
    next_id = allocate_next_setup_thread_id(base, existing)
    return NewThreadResponse(thread_id=next_id)


@router.post("/organizations/{organization_id}/chat/stream")
async def stream_chat(
    organization_id: str,
    data: ChatStreamRequest,
    request: Request,
) -> StreamingResponse:
    async def _stream_with_session():
        async with SessionFactory() as session:
            service = chat_service(session, request, organization_id, thread_id=data.thread_id)
            service.tool_context.mode = data.mode
            async for chunk in service.stream_chat(data, fastapi_request=request):
                yield chunk

    return StreamingResponse(
        _stream_with_session(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/organizations/{organization_id}/chat/history", response_model=ChatHistoryRead)
async def get_history(
    organization_id: str,
    session: Session,
    request: Request,
    thread_id: str | None = None,
) -> ChatHistoryRead:
    service = chat_service(session, request, organization_id, thread_id=thread_id)
    return await service.get_history()


@router.delete("/organizations/{organization_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    organization_id: str,
    session: Session,
    request: Request,
    thread_id: str | None = None,
) -> None:
    service = chat_service(session, request, organization_id, thread_id=thread_id)
    await service.clear_chat()


@router.delete("/organizations/{organization_id}/chat/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    organization_id: str,
    message_id: str,
    session: Session,
    request: Request,
    thread_id: str | None = None,
) -> None:
    service = chat_service(session, request, organization_id, thread_id=thread_id)
    success = await service.delete_message(message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message {message_id}",
        )
