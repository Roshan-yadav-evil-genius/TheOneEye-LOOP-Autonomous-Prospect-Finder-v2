"""Agent-runtime process shell (RecreationDocs foundation apps/agent-runtime)."""

from __future__ import annotations

import asyncio
import logging

from cli import worker

logger = logging.getLogger("loop.agent_runtime")


def main() -> None:
    """Run durable agent effort workers until interrupted."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting LOOP agent-runtime worker shell")
    worker()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        asyncio.get_event_loop().stop()
