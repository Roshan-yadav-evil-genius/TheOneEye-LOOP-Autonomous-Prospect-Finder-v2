import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import DomainError, utcnow
from core.config import get_settings
from observability.logging import get_logger
from observability.telemetry import DLQ_DEPTH, JOB_OUTCOMES
from persistence import models

JobHandler = Callable[[dict[str, Any]], Awaitable[None]]
log = get_logger("loop.jobs")


class JobRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, JobHandler] = {}

    def register(self, key: str, handler: JobHandler) -> None:
        self._handlers[key] = handler

    def get(self, key: str) -> JobHandler:
        if key not in self._handlers:
            raise DomainError("job_handler_not_found", f"No handler is registered for {key}.")
        return self._handlers[key]


class JobService:
    def __init__(self, session: AsyncSession, registry: JobRegistry) -> None:
        self.session = session
        self.registry = registry

    async def enqueue(self, task_key: str, payload: dict[str, Any]) -> models.JobRun:
        row = models.JobRun(task_key=task_key, payload=payload)
        self.session.add(row)
        await self.session.commit()
        return row

    async def run_next(self) -> models.JobRun | None:
        now = utcnow()
        row = await self.session.scalar(
            select(models.JobRun)
            .where(
                models.JobRun.status.in_(("queued", "retry")),
                models.JobRun.available_at <= now,
            )
            .order_by(models.JobRun.available_at)
        )
        if not row:
            return None
        row.status = "running"
        row.started_at = now
        row.attempts += 1
        await self.session.commit()
        log.info(
            "job_claimed",
            job_id=row.id,
            task_key=row.task_key,
            attempt=row.attempts,
            payload=row.payload,
        )
        try:
            await self.registry.get(row.task_key)(row.payload)
            await self.session.refresh(row)
            if row.status == "cancelled":
                JOB_OUTCOMES.labels(row.task_key, "cancelled").inc()
                log.info("job_cancelled", job_id=row.id, task_key=row.task_key)
                return row
            row.status = "completed"
            row.completed_at = utcnow()
            JOB_OUTCOMES.labels(row.task_key, "completed").inc()
            log.info("job_completed", job_id=row.id, task_key=row.task_key)
        except asyncio.CancelledError:
            row.status = "cancelled"
            row.completed_at = utcnow()
            row.error = "cancelled"
            JOB_OUTCOMES.labels(row.task_key, "cancelled").inc()
            log.warning("job_cancelled_error", job_id=row.id, task_key=row.task_key)
        except Exception as exc:
            settings = get_settings()
            row.error = str(exc)
            if row.attempts >= settings.max_job_attempts:
                row.status = "dead_letter"
                JOB_OUTCOMES.labels(row.task_key, "dead_letter").inc()
                DLQ_DEPTH.labels(row.task_key).inc()
                self.session.add(
                    models.DeadLetter(
                        queue=row.task_key,
                        job_run_id=row.id,
                        reason=str(exc),
                        attempts=row.attempts,
                        payload=row.payload,
                    )
                )
                log.exception(
                    "job_dead_letter",
                    job_id=row.id,
                    task_key=row.task_key,
                    attempts=row.attempts,
                    error=str(exc),
                )
            else:
                row.status = "retry"
                JOB_OUTCOMES.labels(row.task_key, "retry").inc()
                delay = settings.job_retry_base_seconds * (2 ** (row.attempts - 1))
                row.available_at = utcnow() + timedelta(seconds=delay)
                log.exception(
                    "job_retry_scheduled",
                    job_id=row.id,
                    task_key=row.task_key,
                    attempts=row.attempts,
                    retry_in_seconds=delay,
                    error=str(exc),
                )
        await self.session.commit()
        return row

    async def replay(self, dead_letter_id: str) -> models.JobRun | models.IntegrationEvent:
        dead = await self.session.get(models.DeadLetter, dead_letter_id)
        if not dead or dead.replay_state == "discarded":
            raise DomainError("dead_letter_not_found", "Dead letter was not found.", 404)
        if "event_type" in dead.payload:
            event = models.IntegrationEvent(
                event_type=dead.payload["event_type"],
                payload=dead.payload.get("payload", {}),
            )
            self.session.add(event)
            dead.replay_state = "replayed"
            await self.session.commit()
            return event
        dead.replay_state = "replayed"
        return await self.enqueue(dead.queue, dead.payload)

    async def discard(self, dead_letter_id: str) -> None:
        dead = await self.session.get(models.DeadLetter, dead_letter_id)
        if not dead:
            raise DomainError("dead_letter_not_found", "Dead letter was not found.", 404)
        dead.replay_state = "discarded"
        await self.session.commit()

    async def loop(self, stop: asyncio.Event, interval_seconds: float = 1) -> None:
        """Durable worker loop with graceful stop for Compose/K8s workers."""
        while not stop.is_set():
            await self.run_next()
            await asyncio.sleep(interval_seconds)


class Scheduler:
    def __init__(self, session: AsyncSession, jobs: JobService) -> None:
        self.session = session
        self.jobs = jobs

    async def tick(self) -> int:
        now = utcnow()
        tasks = (
            await self.session.scalars(
                select(models.ScheduledTask).where(
                    models.ScheduledTask.enabled.is_(True),
                    models.ScheduledTask.next_run_at <= now,
                )
            )
        ).all()
        enqueued = 0
        for task in tasks:
            active = await self.session.scalar(
                select(models.JobRun).where(
                    models.JobRun.task_key == task.key,
                    models.JobRun.status.in_(("queued", "retry", "running")),
                )
            )
            if not active or task.overlap_policy == "queue":
                await self.jobs.enqueue(task.key, task.payload)
                enqueued += 1
            task.next_run_at = now + timedelta(seconds=task.interval_seconds)
        await self.session.commit()
        return enqueued

    async def loop(self, stop: asyncio.Event, interval_seconds: float = 1) -> None:
        while not stop.is_set():
            await self.tick()
            await asyncio.sleep(interval_seconds)
