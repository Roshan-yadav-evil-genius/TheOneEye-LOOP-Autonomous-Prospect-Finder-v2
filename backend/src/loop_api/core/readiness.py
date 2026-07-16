import asyncio
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from loop_api.core.config import Settings
from loop_api.core.database_urls import sqlite_db_file_path
from loop_api.core.schemas import DependencyCheck

_DEFAULT_PORTS = {
    "postgres": 5432,
    "postgresql": 5432,
    "redis": 6379,
}


async def check_tcp_dependency(
    *,
    name: str,
    url: str,
    timeout_seconds: float,
) -> DependencyCheck:
    """Check whether a configured TCP dependency accepts connections."""

    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or _DEFAULT_PORTS.get(parsed.scheme)
    if not host or not port:
        return DependencyCheck(name=name, status="unavailable", detail="invalid URL")

    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout_seconds,
        )
        writer.close()
        await writer.wait_closed()
    except (TimeoutError, OSError):
        return DependencyCheck(name=name, status="unavailable", detail="connection failed")

    return DependencyCheck(name=name, status="ok")


def _ping_sqlite_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=1.0)
    try:
        connection.execute("SELECT 1")
    finally:
        connection.close()


async def check_sqlite_dependency(*, name: str, url: str) -> DependencyCheck:
    """Check that the main SQLite database file can be opened."""

    if not url.startswith("sqlite:"):
        return DependencyCheck(name=name, status="unavailable", detail="expected sqlite URL")

    if ":memory:" in url or "mode=memory" in url:
        return DependencyCheck(name=name, status="ok")

    db_path = sqlite_db_file_path(url)
    if db_path is None:
        return DependencyCheck(name=name, status="unavailable", detail="invalid URL")

    try:
        await asyncio.to_thread(_ping_sqlite_file, db_path)
    except OSError:
        return DependencyCheck(name=name, status="unavailable", detail="connection failed")

    return DependencyCheck(name=name, status="ok")


async def check_threads_postgres_dependency(settings: Settings) -> DependencyCheck:
    """Check LangChain threads PostgreSQL when the threads feature is enabled."""

    threads_url = settings.resolved_threads_database_url
    if not threads_url:
        return DependencyCheck(
            name="postgresql_threads",
            status="unavailable",
            detail="LOOP_THREADS_DATABASE_URL is not configured",
        )

    return await check_tcp_dependency(
        name="postgresql_threads",
        url=threads_url,
        timeout_seconds=settings.dependency_timeout_seconds,
    )


async def collect_readiness_checks(settings: Settings) -> list[DependencyCheck]:
    """Build dependency checks for the readiness endpoint."""

    checks = await asyncio.gather(
        check_sqlite_dependency(name="sqlite", url=settings.resolved_database_url),
        check_tcp_dependency(
            name="redis",
            url=settings.redis_url,
            timeout_seconds=settings.dependency_timeout_seconds,
        ),
    )
    result = list(checks)
    if settings.threads_enabled:
        result.append(await check_threads_postgres_dependency(settings))
    return result
