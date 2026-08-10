from typing import Any, cast

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from core.config import get_settings


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

    async def search_threads(
        self,
        prefix: str | None = None,
        suffix: str | None = None,
        contains: str | None = None,
    ) -> list[str]:
        if not self.database_url:
            return []
        async with AsyncConnectionPool(
            self.database_url, open=False, kwargs={"autocommit": True, "row_factory": dict_row}
        ) as pool:
            await pool.open()
            async with pool.connection() as connection:
                conditions = []
                params: list[str] = []
                if prefix:
                    conditions.append("thread_id LIKE %s")
                    params.append(f"{prefix}%")
                if suffix:
                    conditions.append("thread_id LIKE %s")
                    params.append(f"%{suffix}")
                if contains:
                    conditions.append("thread_id LIKE %s")
                    params.append(f"%{contains}%")

                where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
                query = f"SELECT DISTINCT thread_id FROM checkpoints{where_clause} ORDER BY thread_id"
                rows = await connection.execute(query, tuple(params))
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

    async def list_namespaces(self, thread_id: str) -> list[str]:
        if not self.database_url:
            return []
        async with AsyncConnectionPool(
            self.database_url, open=False, kwargs={"autocommit": True, "row_factory": dict_row}
        ) as pool:
            await pool.open()
            async with pool.connection() as connection:
                rows = await connection.execute(
                    "SELECT checkpoint_ns FROM checkpoints "
                    "WHERE thread_id = %s GROUP BY checkpoint_ns ORDER BY MIN(checkpoint_id) ASC",
                    (thread_id,),
                )
                return [cast(dict[str, Any], row)["checkpoint_ns"] async for row in rows]

