"""Idempotent inbox consumers and progress projection reconciliation."""

from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import LoopService, utcnow
from persistence import models


class EventConsumer:
    """Idempotent inbox consumer for versioned integration events."""

    def __init__(self, session: AsyncSession, consumer_name: str) -> None:
        self.session = session
        self.consumer_name = consumer_name

    async def already_processed(self, event_id: str) -> bool:
        row = await self.session.scalar(
            select(models.ConsumerInbox).where(
                models.ConsumerInbox.consumer == self.consumer_name,
                models.ConsumerInbox.event_id == event_id,
                models.ConsumerInbox.status == "processed",
            )
        )
        return row is not None

    async def mark_processed(self, event_id: str) -> None:
        existing = await self.session.scalar(
            select(models.ConsumerInbox).where(
                models.ConsumerInbox.consumer == self.consumer_name,
                models.ConsumerInbox.event_id == event_id,
            )
        )
        if existing:
            existing.status = "processed"
            existing.processed_at = utcnow()
        else:
            self.session.add(
                models.ConsumerInbox(
                    consumer=self.consumer_name,
                    event_id=event_id,
                    status="processed",
                    processed_at=utcnow(),
                )
            )
        await self.session.commit()

    async def project(self, event: models.IntegrationEvent) -> None:
        """Apply consumer-specific side effects after inbox claim."""
        if self.consumer_name == "audit":
            self.session.add(
                models.AuditEvent(
                    actor="event-consumer",
                    action=event.event_type,
                    entity_type="integration_event",
                    entity_id=event.id,
                    after=event.payload,
                    request_id=event.correlation_id,
                )
            )
            await self.session.commit()
            return
        if self.consumer_name == "progress" and "sales_strategy_id" in event.payload:
            # Progress is OLTP-derived; consumer only records reconciliation heartbeat.
            strategy_id = str(event.payload["sales_strategy_id"])
            progress = await LoopService(self.session).progress(strategy_id)
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="projection",
                    level="info",
                    event_code="progress_reconciled",
                    message=(
                        f"{event.event_type}: companies={progress.companies_registered}/"
                        f"{progress.target_companies} contacts={progress.contacts_registered}/"
                        f"{progress.contacts_target}"
                    ),
                )
            )
            await self.session.commit()

    async def handle(self, event: models.IntegrationEvent) -> bool:
        if await self.already_processed(event.id):
            return False
        await self.project(event)
        await self.mark_processed(event.id)
        return True


def _field(fields: dict[Any, Any], key: str) -> str:
    value = fields.get(key.encode() if any(isinstance(k, bytes) for k in fields) else key)
    if value is None:
        value = fields.get(key)
    if isinstance(value, bytes):
        return value.decode()
    return str(value or "")


class StreamEventConsumer:
    """Reads Redis Streams and fan-out to named EventConsumer handlers."""

    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
        *,
        stream: str = "loop:events",
        group: str = "loop-workers",
        consumer_name: str = "worker-1",
    ) -> None:
        self.session = session
        self.redis = redis
        self.stream = stream
        self.group = group
        self.consumer_name = consumer_name

    async def ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception:
            return

    async def consume_once(self, handlers: list[EventConsumer]) -> int:
        await self.ensure_group()
        raw: Any = await self.redis.xreadgroup(
            self.group,
            self.consumer_name,
            {self.stream: ">"},
            count=20,
            block=1000,
        )
        processed = 0
        for _stream_name, entries in raw or []:
            for message_id, fields in entries:
                event_id = _field(fields, "id") or str(message_id)
                event = await self.session.get(models.IntegrationEvent, event_id)
                if event is None:
                    payload_raw = _field(fields, "payload") or "{}"
                    event = models.IntegrationEvent(
                        id=event_id,
                        event_type=_field(fields, "type") or "Unknown",
                        payload=json.loads(payload_raw),
                    )
                for handler in handlers:
                    if await handler.handle(event):
                        processed += 1
                await self.redis.xack(self.stream, self.group, message_id)
        return processed


async def reconcile_progress(session: AsyncSession, strategy_id: str) -> dict[str, Any]:
    """Rebuild progress projection evidence from OLTP source tables."""
    progress = await LoopService(session).progress(strategy_id)
    session.add(
        models.ProcessLog(
            sales_strategy_id=strategy_id,
            role="projection",
            level="info",
            event_code="progress_rebuild",
            message=json.dumps(progress.model_dump(mode="json")),
        )
    )
    await session.commit()
    return progress.model_dump(mode="json")
