"""Logging setup: Rich console handler + rotating file handler; structlog over stdlib."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast

import structlog
from rich.logging import RichHandler

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LOG_DIR = _BACKEND_ROOT / "instance" / "logs"
_SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "access_token",
    "refresh_token",
    "password",
    "api_key",
    "model_api_key",
}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in _SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def _redact_processor(
    _logger: logging.Logger, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    return cast(dict[str, Any], redact(event_dict))


def configure_logging(
    *,
    json_logs: bool = False,
    level: str = "INFO",
    log_dir: Path | str | None = None,
    log_file_name: str = "loop.log",
) -> Path:
    """Configure root logging with Rich console + rotating file handlers.

    Returns the absolute path of the active log file.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logs_path = Path(log_dir) if log_dir is not None else _DEFAULT_LOG_DIR
    logs_path.mkdir(parents=True, exist_ok=True)
    log_file = logs_path / log_file_name

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact_processor,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)

    console = RichHandler(
        rich_tracebacks=True,
        show_path=True,
        markup=False,
        log_time_format="[%X]",
    )
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    bootstrap = structlog.get_logger("loop.logging")
    bootstrap.info(
        "logging_configured",
        json_logs=json_logs,
        level=level.upper(),
        log_file=str(log_file),
    )
    return log_file


def get_logger(name: str = "loop") -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
