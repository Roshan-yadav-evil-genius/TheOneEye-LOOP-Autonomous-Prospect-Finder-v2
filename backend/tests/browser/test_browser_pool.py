import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import DomainError
from browser.policy import BrowserPolicyGuard, BrowserTaskPolicy, compact_snapshot
from browser.pool import BrowserPool
from persistence import models


def test_domain_allowlist_blocks_unknown_hosts() -> None:
    guard = BrowserPolicyGuard(
        BrowserTaskPolicy(allowed_domains=frozenset({"linkedin.com"}))
    )
    with pytest.raises(ValueError):
        guard.validate_navigation("https://evil.example/path")
    guard.validate_navigation("https://www.linkedin.com/in/someone")


def test_compact_snapshot_dedupes_and_truncates() -> None:
    raw = "\n".join(["line a", "line a", "line b"] + [f"x{i}" for i in range(10)])
    compacted = compact_snapshot(raw, max_lines=5)
    assert "line a" in compacted
    assert compacted.count("line a") == 1
    assert "[snapshot truncated]" in compacted


@pytest.mark.asyncio
async def test_browser_lease_exclusive_and_recovery(session: AsyncSession) -> None:
    pool = BrowserPool(session)
    lease = await pool.acquire("effort-1")
    assert lease.state == "leased"
    with pytest.raises(DomainError) as exc:
        await pool.acquire("effort-2")
    assert exc.value.code == "browser_pool_busy"

    # Expire and recover
    from application.loop_service import utcnow
    from datetime import timedelta

    lease.lease_expires_at = utcnow() - timedelta(seconds=1)
    await session.commit()
    recovered = await pool.force_release_expired()
    assert recovered is True
    lease2 = await pool.acquire("effort-2")
    assert lease2.lease_owner == "effort-2"
    await pool.release(lease2.id, "effort-2")
    row = await session.get(models.BrowserSession, lease2.id)
    assert row is not None
    assert row.state == "available"
