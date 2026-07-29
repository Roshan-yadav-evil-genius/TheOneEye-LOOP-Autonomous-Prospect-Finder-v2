from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from agents.runtime import build_org_setup_thread_id
from application.loop_service import LoopService
from application.setup_chat_service import SetupChatService
from agents.setup_chat.org_agent import create_organization_setup_agent
from agents.setup_chat.common import SetupChatToolContext
from contracts.domain import ChatStreamRequest, ChatHistoryRead
from persistence.database import SessionFactory, get_session

router = APIRouter(prefix="/api/v1", tags=["organization-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]

def chat_service(session: AsyncSession, request: Request, organization_id: str) -> SetupChatService:
    loop_service = LoopService(session, getattr(request.state, "request_id", None))
    
    async def verify_entity() -> None:
        await loop_service.get_organization(organization_id)
        
    thread_id = build_org_setup_thread_id(organization_id)
    tool_context = SetupChatToolContext(
        organization_id=organization_id,
        mode="chat", # Set appropriately in stream, but context is updated per stream request later
        service=loop_service,
    )
    
    return SetupChatService(
        thread_id=thread_id,
        verify_entity=verify_entity,
        agent_factory=create_organization_setup_agent,
        tool_context=tool_context
    )


@router.post("/organizations/{organization_id}/chat/stream")
async def stream_chat(
    organization_id: str,
    data: ChatStreamRequest,
    request: Request,
) -> StreamingResponse:
    async def _stream_with_session():
        async with SessionFactory() as session:
            service = chat_service(session, request, organization_id)
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
) -> ChatHistoryRead:
    service = chat_service(session, request, organization_id)
    return await service.get_history()


@router.delete("/organizations/{organization_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    organization_id: str,
    session: Session,
    request: Request,
) -> None:
    service = chat_service(session, request, organization_id)
    await service.clear_chat()
