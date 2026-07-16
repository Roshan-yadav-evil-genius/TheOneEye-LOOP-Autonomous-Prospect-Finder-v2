from pathlib import Path

from loop_api.core.config import Settings, get_settings
from loop_api.core.database_urls import is_dev_loop_database, resolve_sqlite_database_url


def test_resolve_sqlite_relative_to_backend_root(tmp_path: Path) -> None:
    raw = "sqlite:///instance/loop.db"
    resolved = resolve_sqlite_database_url(raw, base_dir=tmp_path)
    assert resolved == f"sqlite:///{(tmp_path / 'instance' / 'loop.db').resolve()}"


def test_settings_default_to_sqlite_main_database() -> None:
    settings = Settings()
    assert settings.database_url.startswith("sqlite:")
    assert settings.resolved_database_url.endswith("instance/loop.db")
    assert settings.threads_enabled is False
    assert settings.resolved_threads_database_url is None


def test_threads_database_url_is_optional_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_THREADS_ENABLED", "false")
    monkeypatch.delenv("LOOP_THREADS_DATABASE_URL", raising=False)
    settings = get_settings()
    assert settings.threads_enabled is False


def test_is_dev_loop_database_detects_default_path() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    uri = resolve_sqlite_database_url("sqlite:///instance/loop.db", base_dir=backend_root)
    assert is_dev_loop_database(uri, base_dir=backend_root)
