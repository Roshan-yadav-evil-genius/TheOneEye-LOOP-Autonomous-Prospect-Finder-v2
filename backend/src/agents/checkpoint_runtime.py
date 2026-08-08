import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from core.config import get_settings


@asynccontextmanager
async def checkpoint_scope() -> AsyncIterator[Any]:
    """PostgreSQL checkpointer when enabled; otherwise in-memory for no-credential local runs."""
    settings = get_settings()
    conn = settings.threads_database_url or os.getenv("LOOP_THREADS_DATABASE_URL")
    if settings.threads_enabled and conn:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        async with AsyncPostgresSaver.from_conn_string(conn) as checkpointer:
            await checkpointer.setup()
            yield checkpointer
        return

    from langgraph.checkpoint.memory import MemorySaver

    yield MemorySaver()


@asynccontextmanager
async def checkpoint_and_store_scope() -> AsyncIterator[tuple[Any, Any]]:
    """PostgreSQL store and checkpointer when enabled; otherwise in-memory for no-credential local runs."""
    settings = get_settings()
    conn = settings.threads_database_url or os.getenv("LOOP_THREADS_DATABASE_URL")
    if settings.threads_enabled and conn:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from langgraph.store.postgres.aio import AsyncPostgresStore

        async with AsyncPostgresStore.from_conn_string(
            conn_string=conn,
            index={
                "dims": 768,
                "embed": "ollama:nomic-embed-text:latest",
            },
        ) as store:
            async with AsyncPostgresSaver.from_conn_string(conn) as checkpointer:
                await store.setup()
                await checkpointer.setup()
                yield checkpointer, store
        return

    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.store.memory import InMemoryStore

    yield MemorySaver(), InMemoryStore()
