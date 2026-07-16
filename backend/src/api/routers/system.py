from fastapi import APIRouter, Response, status

from core.config import get_settings
from core.readiness import collect_readiness_checks
from core.schemas import BuildInfo, HealthStatus
from observability.telemetry import metrics_payload

router = APIRouter(tags=["system"])


@router.get("/health/live", response_model=HealthStatus)
async def liveness() -> HealthStatus:
    settings = get_settings()
    return HealthStatus(service=settings.service_name, status="ok")


@router.get(
    "/health/ready",
    response_model=HealthStatus,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthStatus}},
)
async def readiness(response: Response) -> HealthStatus:
    settings = get_settings()
    checks = await collect_readiness_checks(settings)
    is_ready = all(check.status == "ok" for check in checks)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthStatus(
        service=settings.service_name,
        status="ok" if is_ready else "not_ready",
        checks=list(checks),
    )


@router.get("/version", response_model=BuildInfo)
async def version() -> BuildInfo:
    settings = get_settings()
    return BuildInfo(
        version=settings.build_version,
        commit_sha=settings.commit_sha,
        build_timestamp=settings.build_timestamp,
    )


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=metrics_payload(), media_type="text/plain; version=0.0.4")
