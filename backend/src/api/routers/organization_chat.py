from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from application.loop_service import LoopService
from application.organization_chat_service import OrgChatService
from contracts.domain import ChatStreamRequest, ChatHistoryRead
from persistence.database import get_session

router = APIRouter(prefix="/api/v1", tags=["organization-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]


def chat_service(session: AsyncSession, request: Request) -> OrgChatService:
    loop_service = LoopService(session, getattr(request.state, "request_id", None))
    return OrgChatService(loop_service)


@router.post("/organizations/{organization_id}/chat/stream")
async def stream_chat(
    organization_id: str,
    data: ChatStreamRequest,
    session: Session,
    request: Request,
) -> StreamingResponse:
    service = chat_service(session, request)
    return StreamingResponse(
        service.stream_chat(organization_id, data, fastapi_request=request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/organizations/{organization_id}/chat/history", response_model=ChatHistoryRead)
async def get_history(
    organization_id: str,
    session: Session,
    request: Request,
) -> ChatHistoryRead:
    service = chat_service(session, request)
    return await service.get_history(organization_id)


@router.delete("/organizations/{organization_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    organization_id: str,
    session: Session,
    request: Request,
) -> None:
    service = chat_service(session, request)
    await service.clear_chat(organization_id)
