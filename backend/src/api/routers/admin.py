from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.brain import BrainMemoryService
from contracts.domain import (
    AuditEventRead,
    BrainMemoryCreate,
    BrainMemoryRead,
    DeadLetterRead,
    IntegrationEventRead,
    JobRunRead,
    ScheduledTaskCreate,
    ScheduledTaskRead,
)
from persistence import models
from persistence.database import get_session
from workers.consumers import reconcile_progress
from workers.jobs import JobRegistry, JobService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/audit", response_model=list[AuditEventRead])
async def audit(session: Session, limit: int = 100) -> object:
    return (
        await session.scalars(
            select(models.AuditEvent).order_by(models.AuditEvent.created_at.desc()).limit(limit)
        )
    ).all()


@router.post("/schedules", response_model=ScheduledTaskRead)
async def create_schedule(data: ScheduledTaskCreate, session: Session) -> object:
    row = models.ScheduledTask(**data.model_dump())
    session.add(row)
    await session.commit()
    return row


@router.get("/schedules", response_model=list[ScheduledTaskRead])
async def schedules(session: Session) -> object:
    return (await session.scalars(select(models.ScheduledTask))).all()


@router.patch("/schedules/{schedule_id}", response_model=ScheduledTaskRead)
async def patch_schedule(
    schedule_id: str, session: Session, enabled: bool | None = None
) -> object:
    row = await session.get(models.ScheduledTask, schedule_id)
    if not row:
        from application.loop_service import DomainError

        raise DomainError("schedule_not_found", "Schedule was not found.", 404)
    if enabled is not None:
        row.enabled = enabled
    await session.commit()
    return row


@router.post("/schedules/{schedule_id}/run-now", response_model=JobRunRead)
async def run_schedule_now(schedule_id: str, session: Session) -> object:
    row = await session.get(models.ScheduledTask, schedule_id)
    if not row:
        from application.loop_service import DomainError

        raise DomainError("schedule_not_found", "Schedule was not found.", 404)
    return await JobService(session, JobRegistry()).enqueue(row.key, row.payload)


@router.post("/sales-strategies/{strategy_id}/progress/reconcile")
async def reconcile(strategy_id: str, session: Session) -> object:
    return await reconcile_progress(session, strategy_id)


@router.get("/jobs", response_model=list[JobRunRead])
async def jobs(session: Session) -> object:
    return (
        await session.scalars(select(models.JobRun).order_by(models.JobRun.created_at.desc()))
    ).all()


@router.get("/dead-letters", response_model=list[DeadLetterRead])
async def dead_letters(session: Session) -> object:
    return (
        await session.scalars(
            select(models.DeadLetter).order_by(models.DeadLetter.created_at.desc())
        )
    ).all()


@router.post(
    "/dead-letters/{dead_letter_id}/replay",
    response_model=JobRunRead | IntegrationEventRead,
)
async def replay(dead_letter_id: str, session: Session) -> object:
    return await JobService(session, JobRegistry()).replay(dead_letter_id)


@router.post("/dead-letters/{dead_letter_id}/discard", status_code=status.HTTP_204_NO_CONTENT)
async def discard(dead_letter_id: str, session: Session) -> None:
    await JobService(session, JobRegistry()).discard(dead_letter_id)


@router.post("/sales-strategies/{strategy_id}/memory", response_model=BrainMemoryRead)
async def remember(strategy_id: str, data: BrainMemoryCreate, session: Session) -> object:
    return await BrainMemoryService(session).remember(strategy_id=strategy_id, **data.model_dump())


@router.get("/sales-strategies/{strategy_id}/memory", response_model=list[BrainMemoryRead])
async def recall(strategy_id: str, agent_type: str, query: str, session: Session) -> object:
    return await BrainMemoryService(session).recall(
        strategy_id=strategy_id, agent_type=agent_type, query=query
    )
