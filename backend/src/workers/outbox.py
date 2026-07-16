import json
from dataclasses import dataclass
from datetime import timedelta

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import utcnow
from core.config import get_settings
from observability.telemetry import DLQ_DEPTH, OUTBOX_PUBLISHED
from persistence import models


@dataclass(frozen=True)
class PublishResult:
    published: int
    failed: int


class OutboxPublisher:
    """Publishes committed integration events to the required Redis Stream."""

    def __init__(self, session: AsyncSession, redis: Redis, stream: str = "loop:events") -> None:
        self.session = session
        self.redis = redis
        self.stream = stream

    async def publish_batch(self, limit: int = 100) -> PublishResult:
        events = (
            await self.session.scalars(
                select(models.IntegrationEvent)
                .where(
                    models.IntegrationEvent.published_at.is_(None),
                    models.IntegrationEvent.dead_lettered_at.is_(None),
                    models.IntegrationEvent.available_at <= utcnow(),
                )
                .order_by(models.IntegrationEvent.created_at)
                .limit(limit)
            )
        ).all()
        published = 0
        failed = 0
        for event in events:
            try:
                await self.redis.xadd(
                    self.stream,
                    {
                        "id": event.id,
                        "type": event.event_type,
                        "version": str(event.version),
                        "correlation_id": event.correlation_id or "",
                        "payload": json.dumps(event.payload),
                    },
                )
                event.published_at = utcnow()
                published += 1
                OUTBOX_PUBLISHED.labels(event.event_type).inc()
            except Exception as exc:
                event.attempts += 1
                event.last_error = str(exc)
                settings = get_settings()
                if event.attempts >= settings.max_job_attempts:
                    event.dead_lettered_at = utcnow()
                    DLQ_DEPTH.labels(self.stream).inc()
                    self.session.add(
                        models.DeadLetter(
                            queue=self.stream,
                            job_run_id=event.id,
                            reason=str(exc),
                            attempts=event.attempts,
                            payload={
                                "event_type": event.event_type,
                                "payload": event.payload,
                            },
                        )
                    )
                else:
                    event.available_at = utcnow() + timedelta(
                        seconds=settings.job_retry_base_seconds * (2 ** (event.attempts - 1))
                    )
                failed += 1
        await self.session.commit()
        return PublishResult(published=published, failed=failed)
