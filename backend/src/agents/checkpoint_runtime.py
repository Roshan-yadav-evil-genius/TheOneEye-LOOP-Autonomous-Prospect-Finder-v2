from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from core.config import get_settings


@asynccontextmanager
async def checkpoint_scope() -> AsyncIterator[Any]:
    """PostgreSQL checkpointer when enabled; otherwise in-memory for no-credential local runs.

    Production workflows require ``LOOP_THREADS_ENABLED`` + ``LOOP_THREADS_DATABASE_URL``.
    Deterministic/local agent construction may proceed without credentials using MemorySaver.
    """
    settings = get_settings()
    if settings.threads_enabled and settings.threads_database_url:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        conn = settings.threads_database_url
        async with AsyncPostgresSaver.from_conn_string(conn) as checkpointer:
            await checkpointer.setup()
            yield checkpointer
        return

    from langgraph.checkpoint.memory import MemorySaver

    yield MemorySaver()
