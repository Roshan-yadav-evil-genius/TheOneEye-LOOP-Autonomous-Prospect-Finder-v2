"""Cooperative cancel signals for in-flight Company/Contact Finder efforts."""

from __future__ import annotations

import asyncio
from typing import Any, TypeVar

T = TypeVar("T")

_EVENTS: dict[tuple[str, str], asyncio.Event] = {}
_LOCK = asyncio.Lock()


def _key(strategy_id: str, role: str) -> tuple[str, str]:
    return (strategy_id, role.replace("_", "-"))


def cancel_event(strategy_id: str, role: str) -> asyncio.Event:
    key = _key(strategy_id, role)
    if key not in _EVENTS:
        _EVENTS[key] = asyncio.Event()
    return _EVENTS[key]


def request_cancel(strategy_id: str, role: str) -> None:
    cancel_event(strategy_id, role).set()


def clear_cancel(strategy_id: str, role: str) -> None:
    cancel_event(strategy_id, role).clear()


def is_cancel_requested(strategy_id: str, role: str) -> bool:
    return cancel_event(strategy_id, role).is_set()


async def run_cancellable(
    strategy_id: str,
    role: str,
    coro: Any,
) -> Any:
    """Run ``coro`` until completion or an operator stop cancel signal."""
    clear_cancel(strategy_id, role)
    task = asyncio.ensure_future(coro)
    cancel_waiter = asyncio.ensure_future(cancel_event(strategy_id, role).wait())
    done, _pending = await asyncio.wait(
        {task, cancel_waiter}, return_when=asyncio.FIRST_COMPLETED
    )
    if cancel_waiter in done and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        raise asyncio.CancelledError(f"{role} effort cancelled for {strategy_id}")
    cancel_waiter.cancel()
    try:
        await cancel_waiter
    except asyncio.CancelledError:
        pass
    return task.result()
