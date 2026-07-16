"""Browser policy and worker chaos-style recovery tests."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from loop_api.application.loop_service import utcnow
from loop_api.browser.policy import BrowserPolicyGuard, BrowserTaskPolicy, compact_snapshot
from loop_api.core.config import get_settings
from loop_api.persistence import models
from loop_api.persistence.database import Base
from loop_api.workers.jobs import JobRegistry, JobService, Scheduler


def test_browser_policy_rejects_non_allowlisted_host() -> None:
    guard = BrowserPolicyGuard(
        BrowserTaskPolicy(allowed_domains=frozenset({"linkedin.com", "example.com"}))
    )
    with pytest.raises(ValueError):
        guard.validate_navigation("https://evil.example/path")
    guard.validate_navigation("https://www.linkedin.com/in/ada")


def test_browser_snapshot_compaction_dedupes_noise() -> None:
    raw = "\n".join(["link A", "link A", "", "  link B  ", "link B"] * 200)
    compacted = compact_snapshot(raw, max_lines=10)
    assert "[snapshot truncated]" in compacted
    assert "link A" in compacted
    assert "link B" in compacted


@pytest.mark.asyncio
async def test_scheduler_skip_overlap_and_job_retry_to_dlq(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LOOP_MAX_JOB_ATTEMPTS", "2")
    monkeypatch.setenv("LOOP_JOB_RETRY_BASE_SECONDS", "0.01")
    get_settings.cache_clear()
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chaos.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        registry = JobRegistry()

        async def boom(_payload: dict) -> None:
            raise RuntimeError("poison")

        registry.register("poison-task", boom)
        jobs = JobService(session, registry)
        session.add(
            models.ScheduledTask(
                key="poison-task",
                interval_seconds=60,
                enabled=True,
                overlap_policy="skip",
                payload={},
            )
        )
        await session.commit()
        assert await Scheduler(session, jobs).tick() == 1
        assert await Scheduler(session, jobs).tick() == 0
        first = await jobs.run_next()
        assert first is not None and first.status == "retry"
        first.available_at = utcnow()
        await session.commit()
        second = await jobs.run_next()
        assert second is not None and second.status == "dead_letter"
        dead = await session.scalar(select(models.DeadLetter))
        assert dead is not None
        replayed = await jobs.replay(dead.id)
        assert replayed.status == "queued"
    await engine.dispose()
    get_settings.cache_clear()
