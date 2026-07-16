from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from loop_api.core.config import Settings
from loop_api.core.readiness import (
    check_sqlite_dependency,
    check_threads_postgres_dependency,
    collect_readiness_checks,
)
from loop_api.core.schemas import DependencyCheck


@pytest.mark.asyncio
async def test_check_sqlite_dependency_uses_temp_file(tmp_path: Path) -> None:
    db_file = tmp_path / "main.sqlite"
    url = f"sqlite:///{db_file}"

    check = await check_sqlite_dependency(name="sqlite", url=url)

    assert check.status == "ok"
    assert db_file.exists()


@pytest.mark.asyncio
async def test_collect_readiness_checks_skips_threads_postgres_by_default(
    monkeypatch,
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "main.sqlite"
    monkeypatch.setenv("LOOP_DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("LOOP_THREADS_ENABLED", "false")

    with patch(
        "loop_api.core.readiness.check_tcp_dependency",
        new_callable=AsyncMock,
        return_value=DependencyCheck(name="redis", status="ok"),
    ):
        settings = Settings()
        checks = await collect_readiness_checks(settings)

    assert [check.name for check in checks] == ["sqlite", "redis"]


@pytest.mark.asyncio
async def test_collect_readiness_checks_requires_threads_url_when_enabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "main.sqlite"
    monkeypatch.setenv("LOOP_DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("LOOP_THREADS_ENABLED", "true")
    monkeypatch.delenv("LOOP_THREADS_DATABASE_URL", raising=False)

    with patch(
        "loop_api.core.readiness.check_tcp_dependency",
        new_callable=AsyncMock,
        return_value=DependencyCheck(name="redis", status="ok"),
    ):
        settings = Settings()
        checks = await collect_readiness_checks(settings)

    threads_check = next(check for check in checks if check.name == "postgresql_threads")
    assert threads_check.status == "unavailable"
    assert "not configured" in (threads_check.detail or "")


@pytest.mark.asyncio
async def test_check_threads_postgres_dependency_reports_missing_url() -> None:
    settings = Settings(threads_enabled=True, threads_database_url="")

    check = await check_threads_postgres_dependency(settings)

    assert check.name == "postgresql_threads"
    assert check.status == "unavailable"
