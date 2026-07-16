from typing import Any, cast

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from loop_api.core.config import get_settings


class ThreadCheckpointStore:
    """PostgreSQL-only adapter for LangGraph checkpoint inspection."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or get_settings().resolved_threads_database_url

    async def list_threads(self, effort_prefix: str) -> list[str]:
        if not self.database_url:
            return []
        async with AsyncConnectionPool(
            self.database_url, open=False, kwargs={"autocommit": True, "row_factory": dict_row}
        ) as pool:
            await pool.open()
            async with pool.connection() as connection:
                rows = await connection.execute(
                    "SELECT DISTINCT thread_id FROM checkpoints "
                    "WHERE thread_id LIKE %s ORDER BY thread_id",
                    (f"{effort_prefix}_%",),
                )
                return [cast(dict[str, Any], row)["thread_id"] async for row in rows]

    async def latest(self, thread_id: str) -> dict[str, Any] | None:
        if not self.database_url:
            return None
        async with AsyncConnectionPool(
            self.database_url, open=False, kwargs={"autocommit": True, "row_factory": dict_row}
        ) as pool:
            await pool.open()
            async with pool.connection() as connection:
                cursor = await connection.execute(
                    "SELECT checkpoint, metadata FROM checkpoints "
                    "WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1",
                    (thread_id,),
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
