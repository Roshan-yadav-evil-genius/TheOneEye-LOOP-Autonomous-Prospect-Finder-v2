"""Pytest configuration for LOOP backend agent tests."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

# Must run before persistence.database import (settings are cached).
os.environ["LOOP_MODEL_PROVIDER"] = "deterministic"
os.environ["LOOP_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOOP_THREADS_ENABLED"] = "false"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings

get_settings.cache_clear()


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    from persistence.database import Base
    import persistence.models  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()
