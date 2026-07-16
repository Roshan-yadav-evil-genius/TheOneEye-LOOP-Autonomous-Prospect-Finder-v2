from typing import Any, Literal

from pydantic import BaseModel, Field


class BuildInfo(BaseModel):
    version: str
    commit_sha: str
    build_timestamp: str


class DependencyCheck(BaseModel):
    name: str
    status: Literal["ok", "unavailable"]
    detail: str | None = None


class HealthStatus(BaseModel):
    service: str
    status: Literal["ok", "not_ready"]
    checks: list[DependencyCheck] = Field(default_factory=list)


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str
