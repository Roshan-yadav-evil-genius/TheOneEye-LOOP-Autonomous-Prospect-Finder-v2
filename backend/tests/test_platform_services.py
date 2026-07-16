import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from loop_api.agents.brain import BrainMemoryService, similarity
from loop_api.agents.model_provider import DeterministicDiscoveryModel
from loop_api.browser.policy import BrowserPolicyGuard, BrowserTaskPolicy, compact_snapshot
from loop_api.persistence import models
from loop_api.persistence.database import Base
from loop_api.workers.jobs import JobRegistry, JobService


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as value:
        yield value
    await engine.dispose()


async def test_brain_memory_is_strategy_scoped_and_ranked(session) -> None:
    strategy = models.SalesStrategy(
        id="strategy-a",
        product_id="product-a",
        name="A",
        sales_strategy_form={},
        target_companies=1,
        contacts_per_company_default=1,
    )
    product = models.Product(
        id="product-a",
        organization_id="org-a",
        name="P",
        kind="product",
    )
    organization = models.Organization(id="org-a", name="O", website="https://example.com")
    session.add_all([organization, product, strategy])
    await session.commit()
    brain = BrainMemoryService(session)
    await brain.remember(
        strategy_id="strategy-a",
        agent_type="company_finder",
        category="insights",
        content="Logistics companies respond to automation signals.",
    )
    results = await brain.recall(
        strategy_id="strategy-a", agent_type="company_finder", query="logistics automation"
    )
    assert [row.category for row in results] == ["insights"]
    assert similarity(["logistics"], ["logistics"]) == 1


async def test_jobs_retry_then_complete(session) -> None:
    calls = 0

    async def flaky(_: dict) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary")

    registry = JobRegistry()
    registry.register("flaky", flaky)
    service = JobService(session, registry)
    job = await service.enqueue("flaky", {})
    await service.run_next()
    assert job.status == "retry"
    job.available_at = job.created_at
    await session.commit()
    await service.run_next()
    assert job.status == "completed"


async def test_deterministic_model_has_safe_no_candidate_default() -> None:
    model = DeterministicDiscoveryModel()
    assert (await model.decide("prompt"))["action"] == "no_candidate"


def test_browser_policy_and_compaction() -> None:
    guard = BrowserPolicyGuard(BrowserTaskPolicy(frozenset({"linkedin.com"})))
    guard.validate_navigation("https://www.linkedin.com/in/test")
    with pytest.raises(ValueError):
        guard.validate_navigation("https://attacker.invalid")
    assert compact_snapshot("button A\nbutton A\n\nbutton B") == "button A\nbutton B"
