"""Server-sent events for process UI refresh (RecreationDocs 04 + 10)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from sqlalchemy import select
from starlette.responses import StreamingResponse

from persistence import models
from persistence.database import SessionFactory

router = APIRouter(prefix="/api/v1", tags=["events"])


async def _process_log_stream(strategy_id: str, role: str, request: Request) -> AsyncIterator[str]:
    last_seen: str | None = None
    while True:
        if await request.is_disconnected():
            break
        async with SessionFactory() as session:
            rows = (
                await session.scalars(
                    select(models.ProcessLog)
                    .where(
                        models.ProcessLog.sales_strategy_id == strategy_id,
                        models.ProcessLog.role == role,
                    )
                    .order_by(models.ProcessLog.created_at.desc())
                    .limit(20)
                )
            ).all()
        newest = rows[0].id if rows else None
        if newest and newest != last_seen:
            last_seen = newest
            payload = [
                {
                    "id": row.id,
                    "event_code": row.event_code,
                    "message": row.message,
                    "level": row.level,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in reversed(rows)
            ]
            yield f"event: process_logs\ndata: {json.dumps(payload)}\n\n"
        else:
            yield "event: ping\ndata: {}\n\n"
        await asyncio.sleep(2)


@router.get("/sales-strategies/{strategy_id}/agents/{role}/events")
async def process_events(strategy_id: str, role: str, request: Request) -> StreamingResponse:
    return StreamingResponse(
        _process_log_stream(strategy_id, role, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
