from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings


class Base(DeclarativeBase):
    pass


def _async_sqlite_url(url: str) -> str:
    return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)


settings = get_settings()
database_url = _async_sqlite_url(settings.resolved_database_url)
db_path = database_url.removeprefix("sqlite+aiosqlite:///")
if db_path and db_path != ":memory:":
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(database_url, future=True)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_integrity(dbapi_connection: object, _record: object) -> None:
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session


async def create_schema() -> None:
    from persistence import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
