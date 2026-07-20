"""Agent-runtime process shell (RecreationDocs foundation apps/agent-runtime)."""

from __future__ import annotations

import asyncio

from cli import worker
from core.config import get_settings
from observability.logging import configure_logging, get_logger

log = get_logger("loop.agent_runtime")


def main() -> None:
    """Run durable agent effort workers until interrupted."""
    settings = get_settings()
    configure_logging(
        json_logs=settings.env in {"staging", "production"},
        level=settings.log_level,
        log_dir=settings.resolved_log_dir,
        log_file_name="loop-worker.log",
    )
    log.info("Starting LOOP agent-runtime worker shell")
    worker()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        asyncio.get_event_loop().stop()
