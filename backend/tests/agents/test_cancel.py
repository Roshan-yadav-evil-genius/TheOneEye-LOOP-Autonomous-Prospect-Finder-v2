"""Cancel registry unit tests for immediate process stop."""

import asyncio

import pytest

from agents.cancel import clear_cancel, is_cancel_requested, request_cancel, run_cancellable


@pytest.mark.asyncio
async def test_run_cancellable_aborts_on_stop_signal() -> None:
    clear_cancel("s1", "company-finder")

    async def slow() -> str:
        await asyncio.sleep(5)
        return "done"

    task = asyncio.create_task(run_cancellable("s1", "company-finder", slow()))
    await asyncio.sleep(0.05)
    request_cancel("s1", "company-finder")
    with pytest.raises(asyncio.CancelledError):
        await task
    assert is_cancel_requested("s1", "company-finder")
