"""Browser-pool process shell (RecreationDocs foundation apps/browser-pool)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI

from browser.pool import BrowserPool
from core.config import get_settings
from persistence.database import SessionFactory, create_schema

logger = logging.getLogger("loop.browser_pool")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await create_schema()
    yield


app = FastAPI(title="LOOP Browser Pool", version="0.1.0", lifespan=lifespan)


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"service": "loop-browser-pool", "status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"service": "loop-browser-pool", "status": "ok"}


@app.post("/sessions/acquire")
async def acquire(payload: dict[str, Any]) -> dict[str, Any]:
    effort_id = str(payload.get("effort_id") or "anonymous")
    async with SessionFactory() as session:
        lease = await BrowserPool(session).acquire(effort_id)
        return {
            "session_id": lease.id,
            "profile_id": lease.profile_id,
            "state": lease.state,
            "mcp_url": get_settings().browser_mcp_url,
        }


@app.post("/sessions/{session_id}/release")
async def release(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, str]:
    effort_id = str((payload or {}).get("effort_id") or "")
    async with SessionFactory() as session:
        await BrowserPool(session).release(session_id, effort_id)
    return {"status": "released"}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    logger.info("Starting LOOP browser-pool on MCP URL %s", settings.browser_mcp_url)
    uvicorn.run(
        "loop_api.runtimes.browser_pool:app",
        host=settings.api_host,
        port=8932,
        factory=False,
    )


if __name__ == "__main__":
    main()
