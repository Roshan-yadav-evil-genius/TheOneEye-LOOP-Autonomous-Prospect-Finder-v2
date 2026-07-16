from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from application.loop_service import LoopService
from application.setup_chat_service import SetupChatService
from agents.setup_chat.product_agent import create_product_setup_agent
from agents.setup_chat.common import SetupChatToolContext
from contracts.domain import ChatStreamRequest, ChatHistoryRead
from persistence.database import get_session

router = APIRouter(prefix="/api/v1", tags=["product-chat"])
Session = Annotated[AsyncSession, Depends(get_session)]


def chat_service(session: AsyncSession, request: Request, product_id: str) -> SetupChatService:
    loop_service = LoopService(session, getattr(request.state, "request_id", None))
    
    # We need organization_id for the tool context because product tools can read the org profile
    # The setup_chat_service will verify the product exists and we can get the organization_id from it
    # We fetch it here synchronously to initialize the context, but wait, `chat_service` is sync!
    # I can't await `loop_service.get_product` here.
    # Instead, we can let the `verify_entity` callback do it and set the organization_id on the context?
    # Or, the tool context doesn't need to be fully populated immediately, as long as it is populated before tools run.
    
    tool_context = SetupChatToolContext(
        organization_id="", # Will be set in verify_entity
        product_id=product_id,
        mode="chat",
        service=loop_service,
    )

    async def verify_entity() -> None:
        product = await loop_service.get_product(product_id)
        tool_context.organization_id = product.organization_id
        
    thread_id = f"product_{product_id}_setup_chat"
    
    return SetupChatService(
        thread_id=thread_id,
        verify_entity=verify_entity,
        agent_factory=create_product_setup_agent,
        tool_context=tool_context
    )


@router.post("/products/{product_id}/chat/stream")
async def stream_chat(
    product_id: str,
    data: ChatStreamRequest,
    session: Session,
    request: Request,
) -> StreamingResponse:
    service = chat_service(session, request, product_id)
    service.tool_context.mode = data.mode
    return StreamingResponse(
        service.stream_chat(data, fastapi_request=request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/products/{product_id}/chat/history", response_model=ChatHistoryRead)
async def get_history(
    product_id: str,
    session: Session,
    request: Request,
) -> ChatHistoryRead:
    service = chat_service(session, request, product_id)
    await service.verify_entity() # Initialize org_id in tool context if history needs it, though history only reads checkpointer
    return await service.get_history()


@router.delete("/products/{product_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    product_id: str,
    session: Session,
    request: Request,
) -> None:
    service = chat_service(session, request, product_id)
    await service.clear_chat()
