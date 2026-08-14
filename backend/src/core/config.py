from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.database_urls import resolve_sqlite_database_url

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
class Settings(BaseSettings):
    """Typed twelve-factor configuration for the API shell.

    Main OLTP persistence uses SQLite (``database_url``). LangChain/LangGraph
    effort threads and checkpoints use a separate PostgreSQL instance
    (``threads_database_url``) when ``threads_enabled`` is true.
    """

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_prefix="LOOP_",
        extra="ignore",
    )

    env: Literal["development", "test", "staging", "production"] = "development"
    service_name: str = "loop-api"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=7878, ge=1, le=65535)
    cors_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    database_url: str = ""
    threads_enabled: bool = False
    threads_database_url: str = ""
    redis_url: str = "redis://127.0.0.1:6379/0"
    model_provider: Literal["deterministic", "openai", "ollama"] = "deterministic"
    model_name: str = "deterministic"
    model_base_url: str = ""
    model_api_key: str = ""
    browser_mcp_url: str = "http://127.0.0.1:8931/mcp"
    browser_allowed_domains: str = (
        "linkedin.com,google.com,crunchbase.com,producthunt.com,ycombinator.com,"
        "wellfound.com,github.com"
    )
    browser_action_interval_seconds: float = Field(default=2, ge=0)
    agent_pacing_seconds: float = Field(default=300, ge=0)
    agent_consecutive_failure_limit: int = Field(default=5, ge=1, le=50)
    agent_recursion_limit: int = Field(default=500, ge=10, le=5000)
    planner_prompt_version: Literal["v1", "v2"] = "v2"
    max_job_attempts: int = Field(default=5, ge=1, le=50)
    job_retry_base_seconds: float = Field(default=2, gt=0)
    dependency_timeout_seconds: float = Field(default=0.25, gt=0, le=5)
    build_version: str = "0.1.0"
    commit_sha: str = "local"
    build_timestamp: str = "unknown"
    log_level: str = "INFO"
    log_dir: str = ""
    log_file_name: str = "loop.log"

    @field_validator("threads_database_url", mode="before")
    @classmethod
    def _strip_threads_database_url(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        """Main SQLite URL with relative paths anchored to the backend root."""
        url = self.database_url.strip()
        if not url:
            url = f"sqlite:///instance/{self.env}/db/loop.db"
            
        if url.startswith("sqlite:///"):
            path_str = url.replace("sqlite:///", "")
            path = Path(path_str)
            if not path.is_absolute():
                path = _BACKEND_ROOT / path
            path.parent.mkdir(parents=True, exist_ok=True)
            
        return resolve_sqlite_database_url(url, base_dir=_BACKEND_ROOT)

    @property
    def resolved_threads_database_url(self) -> str | None:
        """PostgreSQL URL for LangChain threads when configured."""
        url = self.threads_database_url.strip()
        return url or None

    @property
    def resolved_log_dir(self) -> Path:
        """Directory for rotating application logs (defaults to backend/instance/logs)."""
        raw = self.log_dir.strip()
        if not raw:
            return _BACKEND_ROOT / "instance" / "logs"
        path = Path(raw)
        return path if path.is_absolute() else _BACKEND_ROOT / path

    @property
    def resolved_upload_dir(self) -> Path:
        """Absolute path to the environment-specific upload directory."""
        return _BACKEND_ROOT / "instance" / self.env / "upload"


@lru_cache
def get_settings() -> Settings:
    return Settings()
