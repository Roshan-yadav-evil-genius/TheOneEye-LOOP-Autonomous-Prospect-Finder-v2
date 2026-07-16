"""Brain memory isolation and compaction tests."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from loop_api.agents.brain import BrainMemoryService
from loop_api.persistence.database import Base


@pytest.mark.asyncio
async def test_brain_memory_is_isolated_by_strategy_and_agent(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'brain.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        service = BrainMemoryService(session)
        await service.remember(
            strategy_id="s1",
            agent_type="company_finder",
            category="insights",
            content="Prefer Series B SaaS lookalikes",
        )
        await service.remember(
            strategy_id="s1",
            agent_type="contact_finder",
            category="insights",
            content="Avoid recruiters for VP Sales target",
        )
        await service.remember(
            strategy_id="s2",
            agent_type="company_finder",
            category="insights",
            content="Ignore healthcare for this strategy",
        )
        company = await service.recall(
            strategy_id="s1", agent_type="company_finder", query="SaaS lookalikes"
        )
        contact = await service.recall(
            strategy_id="s1", agent_type="contact_finder", query="recruiters"
        )
        assert len(company) == 1
        assert "SaaS" in company[0].content
        assert len(contact) == 1
        assert "recruiters" in contact[0].content
        removed = await service.compact(
            strategy_id="s1", agent_type="company_finder", max_entries=0
        )
        assert removed == 1
    await engine.dispose()
