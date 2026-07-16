import asyncio
from datetime import timedelta

import typer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.model_provider import resolve_discovery_model
from agents.orchestration import CompanyFinderEffort, ContactFinderEffort
from application.loop_service import utcnow
from core.config import get_settings
from persistence import models
from persistence.database import SessionFactory, create_schema
from workers.consumers import EventConsumer, StreamEventConsumer, reconcile_progress
from workers.jobs import JobRegistry, JobService, Scheduler
from workers.outbox import OutboxPublisher

app = typer.Typer(help="LOOP API, worker, scheduler, admin, and bootstrap CLI.")


def _registry(session: AsyncSession) -> JobRegistry:
    registry = JobRegistry()

    async def enqueue_next(role: str, strategy_id: str) -> None:
        state = await session.scalar(
            select(models.AgentProcessState).where(
                models.AgentProcessState.sales_strategy_id == strategy_id,
                models.AgentProcessState.role == role,
            )
        )
        if state and state.desired_state == "running":
            session.add(
                models.JobRun(
                    task_key=role,
                    payload={"sales_strategy_id": strategy_id},
                    available_at=utcnow() + timedelta(seconds=get_settings().agent_pacing_seconds),
                )
            )
            await session.commit()

    async def company(payload: dict[str, object]) -> None:
        strategy_id = str(payload["sales_strategy_id"])
        await CompanyFinderEffort(session, resolve_discovery_model()).execute(strategy_id)
        await enqueue_next("company-finder", strategy_id)

    async def contact(payload: dict[str, object]) -> None:
        strategy_id = str(payload["sales_strategy_id"])
        await ContactFinderEffort(session, resolve_discovery_model()).execute(strategy_id)
        await enqueue_next("contact-finder", strategy_id)

    registry.register("company-finder", company)
    registry.register("contact-finder", contact)
    return registry


@app.command()
def bootstrap() -> None:
    """Create SQLite schema for a fresh environment."""
    asyncio.run(create_schema())


@app.command("worker-once")
def worker_once() -> None:
    """Run one durable queued job and one outbox publish batch."""

    async def run() -> None:
        async with SessionFactory() as session:
            await JobService(session, _registry(session)).run_next()
            redis = Redis.from_url(get_settings().redis_url)
            try:
                await OutboxPublisher(session, redis).publish_batch()
            finally:
                await redis.aclose()

    asyncio.run(run())


@app.command()
def worker() -> None:
    """Run the durable worker loop until interrupted."""

    async def run() -> None:
        stop = asyncio.Event()
        redis = Redis.from_url(get_settings().redis_url)
        try:
            while not stop.is_set():
                async with SessionFactory() as session:
                    await JobService(session, _registry(session)).run_next()
                    await OutboxPublisher(session, redis).publish_batch()
                await asyncio.sleep(1)
        finally:
            await redis.aclose()

    asyncio.run(run())


@app.command("scheduler-once")
def scheduler_once() -> None:
    """Evaluate due schedules once."""

    async def run() -> None:
        async with SessionFactory() as session:
            jobs = JobService(session, _registry(session))
            typer.echo(f"enqueued={await Scheduler(session, jobs).tick()}")

    asyncio.run(run())


@app.command()
def scheduler() -> None:
    """Run the scheduler loop until interrupted."""

    async def run() -> None:
        stop = asyncio.Event()
        async with SessionFactory() as session:
            jobs = JobService(session, _registry(session))
            await Scheduler(session, jobs).loop(stop, interval_seconds=5)

    asyncio.run(run())


@app.command("consume-once")
def consume_once() -> None:
    """Consume one Redis Streams batch into idempotent inbox handlers."""

    async def run() -> None:
        async with SessionFactory() as session:
            redis = Redis.from_url(get_settings().redis_url)
            try:
                consumer = StreamEventConsumer(session, redis)
                processed = await consumer.consume_once(
                    [EventConsumer(session, "audit"), EventConsumer(session, "progress")]
                )
                typer.echo(f"processed={processed}")
            finally:
                await redis.aclose()

    asyncio.run(run())


@app.command()
def reconcile(strategy_id: str) -> None:
    """Rebuild progress projection evidence for a sales strategy."""

    async def run() -> None:
        async with SessionFactory() as session:
            typer.echo(await reconcile_progress(session, strategy_id))

    asyncio.run(run())


@app.command()
def seed(
    wipe: bool = typer.Option(
        True,
        "--wipe/--no-wipe",
        help=(
            "Drop and recreate SQLite OLTP tables before seeding (default). "
            "With --no-wipe, skip when seed organizations already exist."
        ),
    ),
) -> None:
    """Seed realistic local SQLite OLTP data for operator E2E workflows.

    Creates 2 organizations, products per org, one sales strategy per product,
    plus companies/contacts/process artifacts on every strategy. Does not
    write PostgreSQL LangChain thread/checkpoint tables.

    Default --wipe recreates tables so local DBs stay aligned with current models.
    """

    async def run() -> None:
        from application.seed_service import SeedService, wipe_oltp_data

        await create_schema()
        wiped = False
        if wipe:
            await wipe_oltp_data()
            wiped = True
        async with SessionFactory() as session:
            summary = await SeedService(session).seed(wiped=wiped)
            for line in summary.as_lines():
                typer.echo(line)

    asyncio.run(run())


@app.command()
def version() -> None:
    typer.echo(get_settings().build_version)


if __name__ == "__main__":
    app()
