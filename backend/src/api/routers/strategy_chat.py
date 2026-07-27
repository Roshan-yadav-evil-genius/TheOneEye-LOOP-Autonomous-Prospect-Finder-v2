from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from application.loop_service import LoopService
from application.setup_chat_service import SetupChatService
from agents.setup_chat.strategy_agent import create_strategy_setup_agent
from agents.setup_chat.common import SetupChatToolContext
from contracts.domain import ChatStreamRequest, ChatHistoryRead
from persistence.database import SessionFactory, get_session

router = APIRouter(prefix="/api/v1", tags=["strategy-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]


def chat_service(session: AsyncSession, request: Request, strategy_id: str) -> SetupChatService:
    loop_service = LoopService(session, getattr(request.state, "request_id", None))
    
    tool_context = SetupChatToolContext(
        organization_id="", 
        product_id="",
        strategy_id=strategy_id,
        mode="chat",
        service=loop_service,
    )

    async def verify_entity() -> None:
        strategy = await loop_service.get_strategy(strategy_id)
        product = await loop_service.get_product(strategy.product_id)
        tool_context.product_id = product.id
        tool_context.organization_id = product.organization_id
        
    thread_id = f"strategy_{strategy_id}_setup_chat"
    
    return SetupChatService(
        thread_id=thread_id,
        verify_entity=verify_entity,
        agent_factory=create_strategy_setup_agent,
        tool_context=tool_context
    )


@router.post("/sales-strategies/{strategy_id}/chat/stream")
async def stream_chat(
    strategy_id: str,
    data: ChatStreamRequest,
    request: Request,
) -> StreamingResponse:
    async def _stream_with_session():
        async with SessionFactory() as session:
            service = chat_service(session, request, strategy_id)
            service.tool_context.mode = data.mode
            async for chunk in service.stream_chat(data, fastapi_request=request):
                yield chunk

    return StreamingResponse(
        _stream_with_session(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/sales-strategies/{strategy_id}/chat/history", response_model=ChatHistoryRead)
async def get_history(
    strategy_id: str,
    session: Session,
    request: Request,
) -> ChatHistoryRead:
    service = chat_service(session, request, strategy_id)
    await service.verify_entity()
    return await service.get_history()


@router.delete("/sales-strategies/{strategy_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    strategy_id: str,
    session: Session,
    request: Request,
) -> None:
    service = chat_service(session, request, strategy_id)
    await service.clear_chat()
