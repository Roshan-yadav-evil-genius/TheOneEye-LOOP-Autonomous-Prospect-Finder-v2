"""Browser-pool process shell (RecreationDocs foundation apps/browser-pool)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from browser.pool import BrowserPool, PlaywrightMcpGateway
from browser.policy import BrowserPolicyGuard, BrowserTaskPolicy
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
async def ready() -> JSONResponse:
    settings = get_settings()
    domains = frozenset(
        part.strip().lower()
        for part in settings.browser_allowed_domains.split(",")
        if part.strip()
    )
    gateway = PlaywrightMcpGateway(
        BrowserPolicyGuard(
            BrowserTaskPolicy(
                allowed_domains=domains,
                minimum_action_interval_seconds=settings.browser_action_interval_seconds,
            )
        )
    )
    healthy = await gateway.health()
    status = "ok" if healthy else "degraded"
    code = 200 if healthy else 503
    return JSONResponse(
        status_code=code,
        content={
            "service": "loop-browser-pool",
            "status": status,
            "mcp_url": settings.browser_mcp_url,
            "mcp_healthy": healthy,
        },
    )


@app.post("/sessions/acquire")
async def acquire(payload: dict[str, Any]) -> dict[str, Any]:
    effort_id = str(payload.get("effort_id") or "anonymous")
    async with SessionFactory() as session:
        pool = BrowserPool(session)
        await pool.force_release_expired()
        lease = await pool.acquire(effort_id)
        return {
            "session_id": lease.id,
            "profile_id": lease.profile_id,
            "state": lease.state,
            "mcp_url": get_settings().browser_mcp_url,
            "lease_owner": lease.lease_owner,
        }


@app.post("/sessions/{session_id}/heartbeat")
async def heartbeat(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    effort_id = str((payload or {}).get("effort_id") or "")
    async with SessionFactory() as session:
        lease = await BrowserPool(session).heartbeat(session_id, effort_id)
        return {
            "session_id": lease.id,
            "state": lease.state,
            "lease_expires_at": lease.lease_expires_at.isoformat()
            if lease.lease_expires_at
            else None,
        }


@app.post("/sessions/{session_id}/release")
async def release(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, str]:
    effort_id = str((payload or {}).get("effort_id") or "")
    async with SessionFactory() as session:
        try:
            await BrowserPool(session).release(session_id, effort_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "released"}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    logger.info("Starting LOOP browser-pool on MCP URL %s", settings.browser_mcp_url)
    uvicorn.run(
        "runtimes.browser_pool:app",
        host=settings.api_host,
        port=8932,
        factory=False,
    )


if __name__ == "__main__":
    main()
