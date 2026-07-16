"""Admin process shell reuses the API mount for DLQ/schedules/memory."""

from loop_api.main import app

__all__ = ["app"]
