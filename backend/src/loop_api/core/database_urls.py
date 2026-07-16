"""Resolve main (SQLite) and threads (PostgreSQL) database URLs."""

from __future__ import annotations

from pathlib import Path

DEV_LOOP_DB_PATH_NAME = "instance/loop.db"
_SQLITE_FILE_PREFIX = "sqlite:///"


def resolve_sqlite_database_url(raw: str, *, base_dir: Path) -> str:
    """Anchor relative SQLite file paths to ``base_dir`` (not the process cwd)."""
    if not raw.startswith("sqlite:"):
        return raw
    if ":memory:" in raw or "mode=memory" in raw:
        return raw
    if not raw.startswith(_SQLITE_FILE_PREFIX):
        return raw

    database = raw[len(_SQLITE_FILE_PREFIX) :]
    if not database:
        return raw

    path = Path(database)
    if path.is_absolute():
        return raw
    absolute = (base_dir / path).resolve()
    return f"{_SQLITE_FILE_PREFIX}{absolute}"


def sqlite_db_file_path(uri: str) -> Path | None:
    """Return the filesystem path for a SQLite URL, if it uses a file-backed database."""
    if not uri.startswith("sqlite:"):
        return None
    if ":memory:" in uri or "mode=memory" in uri:
        return None
    if not uri.startswith(_SQLITE_FILE_PREFIX):
        return None

    database = uri[len(_SQLITE_FILE_PREFIX) :]
    if not database:
        return None
    return Path(database)


def is_dev_loop_database(uri: str, *, base_dir: Path) -> bool:
    """True when the URI points at the default dev SQLite file under ``instance/loop.db``."""
    dev_path = (base_dir / DEV_LOOP_DB_PATH_NAME).resolve()
    path = sqlite_db_file_path(uri)
    return path is not None and path.resolve() == dev_path
