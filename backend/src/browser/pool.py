import asyncio
from datetime import timedelta
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import DomainError, utcnow
from browser.policy import BrowserPolicyGuard
from core.config import get_settings
from observability.telemetry import BROWSER_LEASES
from persistence import models


class BrowserPool:
    """Exclusive lease around the shared operator Playwright MCP session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def acquire(self, effort_id: str, profile_id: str = "operator") -> models.BrowserSession:
        now = utcnow()
        row = await self.session.scalar(
            select(models.BrowserSession).where(
                models.BrowserSession.profile_id == profile_id,
                or_(
                    models.BrowserSession.state == "available",
                    models.BrowserSession.lease_expires_at < now,
                ),
            )
        )
        if not row:
            existing = await self.session.scalar(
                select(models.BrowserSession).where(models.BrowserSession.profile_id == profile_id)
            )
            if existing:
                raise DomainError("browser_pool_busy", "No browser session is currently available.")
            row = models.BrowserSession(profile_id=profile_id)
            self.session.add(row)
        row.state = "leased"
        row.lease_owner = effort_id
        row.leased_at = now
        row.lease_expires_at = now + timedelta(minutes=10)
        row.health = "unknown"
        await self.session.commit()
        BROWSER_LEASES.labels("acquired").inc()
        return row

    async def heartbeat(self, session_id: str, effort_id: str) -> models.BrowserSession:
        row = await self.session.get(models.BrowserSession, session_id)
        if not row or row.lease_owner != effort_id:
            raise DomainError("browser_lease_not_found", "Browser lease was not found.", 404)
        row.lease_expires_at = utcnow() + timedelta(minutes=10)
        await self.session.commit()
        return row

    async def release(self, session_id: str, effort_id: str) -> None:
        row = await self.session.get(models.BrowserSession, session_id)
        if not row or row.lease_owner != effort_id:
            raise DomainError("browser_lease_not_found", "Browser lease was not found.", 404)
        row.state = "available"
        row.lease_owner = None
        row.lease_expires_at = None
        row.health = "ok"
        await self.session.commit()
        BROWSER_LEASES.labels("released").inc()

    async def force_release_expired(self, profile_id: str = "operator") -> bool:
        """Recover from dead owners without duplicate lease ownership."""
        now = utcnow()
        row = await self.session.scalar(
            select(models.BrowserSession).where(
                models.BrowserSession.profile_id == profile_id,
                models.BrowserSession.state == "leased",
                models.BrowserSession.lease_expires_at < now,
            )
        )
        if not row:
            return False
        row.state = "available"
        row.lease_owner = None
        row.lease_expires_at = None
        row.health = "recovered"
        await self.session.commit()
        BROWSER_LEASES.labels("recovered").inc()
        return True


class PlaywrightMcpGateway:
    def __init__(self, guard: BrowserPolicyGuard, endpoint: str | None = None) -> None:
        self.guard = guard
        self.endpoint = endpoint or get_settings().browser_mcp_url
        connection: Any = {"transport": "http", "url": self.endpoint}
        self.client = MultiServerMCPClient({"playwright": connection})

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if "url" in arguments:
            self.guard.validate_navigation(str(arguments["url"]))
        delay = self.guard.seconds_until_next_action()
        if delay:
            await asyncio.sleep(delay)
        async with self.client.session("playwright") as session:
            tools = await load_mcp_tools(session)
            tool = next((candidate for candidate in tools if candidate.name == tool_name), None)
            if not tool:
                raise ValueError(f"Unknown Playwright MCP tool: {tool_name}")
            result = await tool.ainvoke(arguments)
        self.guard.record_action()
        return result

    async def health(self) -> bool:
        try:
            async with self.client.session("playwright"):
                return True
        except Exception:
            return False
