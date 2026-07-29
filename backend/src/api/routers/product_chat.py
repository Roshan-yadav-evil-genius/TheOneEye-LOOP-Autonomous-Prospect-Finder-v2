from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from agents.runtime import build_product_setup_thread_id
from application.loop_service import LoopService
from application.setup_chat_service import SetupChatService
from agents.setup_chat.product_agent import create_product_setup_agent
from agents.setup_chat.common import SetupChatToolContext
from contracts.domain import ChatStreamRequest, ChatHistoryRead
from persistence.database import SessionFactory, get_session

router = APIRouter(prefix="/api/v1", tags=["product-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]


async def chat_service(session: AsyncSession, request: Request, product_id: str) -> SetupChatService:
    loop_service = LoopService(session, getattr(request.state, "request_id", None))
    product = await loop_service.get_product(product_id)
    organization_id = product.organization_id
    
    async def verify_entity() -> None:
        await loop_service.get_product(product_id)
        
    thread_id = build_product_setup_thread_id(organization_id, product_id)
    
    tool_context = SetupChatToolContext(
        organization_id=organization_id,
        product_id=product_id,
        mode="chat",
        service=loop_service,
    )
    
    return SetupChatService(
        thread_id=thread_id,
        verify_entity=verify_entity,
        agent_factory=create_product_setup_agent,
        tool_context=tool_context,
    )


@router.post("/products/{product_id}/chat/stream")
async def stream_chat(
    product_id: str,
    data: ChatStreamRequest,
    request: Request,
) -> StreamingResponse:
    async def _stream_with_session():
        async with SessionFactory() as session:
            service = await chat_service(session, request, product_id)
            service.tool_context.mode = data.mode
            async for chunk in service.stream_chat(data, fastapi_request=request):
                yield chunk

    return StreamingResponse(
        _stream_with_session(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/products/{product_id}/chat/history", response_model=ChatHistoryRead)
async def get_history(
    product_id: str,
    session: Session,
    request: Request,
) -> ChatHistoryRead:
    service = await chat_service(session, request, product_id)
    return await service.get_history()


@router.delete("/products/{product_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    product_id: str,
    session: Session,
    request: Request,
) -> None:
    service = await chat_service(session, request, product_id)
    await service.clear_chat()
