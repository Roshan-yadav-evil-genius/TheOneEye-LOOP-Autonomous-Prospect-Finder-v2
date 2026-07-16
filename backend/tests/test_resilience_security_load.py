import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from loop_api.main import create_app
from loop_api.persistence import models
from loop_api.persistence.database import Base
from loop_api.workers.outbox import OutboxPublisher


async def test_health_endpoint_handles_concurrent_probe_load() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        results = await asyncio.gather(*(client.get("/health/live") for _ in range(50)))
    assert {response.status_code for response in results} == {200}


async def test_untrusted_origin_is_not_granted_cors_access() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.options(
            "/health/live",
            headers={
                "Origin": "https://attacker.invalid",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.headers.get("access-control-allow-origin") is None


async def test_outbox_survives_redis_outage_and_dead_letters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOOP_MAX_JOB_ATTEMPTS", "1")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    class UnavailableRedis:
        async def xadd(self, *_args, **_kwargs):
            raise ConnectionError("redis unavailable")

    async with factory() as session:
        event = models.IntegrationEvent(event_type="test.event", payload={})
        session.add(event)
        await session.commit()
        result = await OutboxPublisher(session, UnavailableRedis()).publish_batch()  # type: ignore[arg-type]
        assert result.failed == 1
        assert event.dead_lettered_at is not None
    await engine.dispose()
