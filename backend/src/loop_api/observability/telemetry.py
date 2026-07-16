from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import Counter, Histogram, generate_latest

from loop_api.core.config import get_settings

REQUEST_COUNT = Counter("loop_http_requests_total", "HTTP requests", ("method", "route", "status"))
REQUEST_DURATION = Histogram(
    "loop_http_request_duration_seconds", "HTTP request latency", ("method", "route")
)
AGENT_EFFORTS = Counter("loop_agent_efforts_total", "Agent efforts", ("role", "outcome"))
OUTBOX_PUBLISHED = Counter(
    "loop_outbox_published_total", "Outbox events published", ("event_type",)
)
DLQ_DEPTH = Counter("loop_dead_letters_total", "Dead-letter enqueues", ("task_key",))
JOB_OUTCOMES = Counter(
    "loop_job_outcomes_total", "Durable job outcomes", ("task_key", "outcome")
)
BROWSER_LEASES = Counter(
    "loop_browser_leases_total", "Browser pool lease events", ("event",)
)


def configure_tracing() -> None:
    if isinstance(trace.get_tracer_provider(), TracerProvider):
        return
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({"service.name": get_settings().service_name}))
    )


async def telemetry_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started = perf_counter()
    route = request.url.path
    tracer = trace.get_tracer("loop-api")
    with tracer.start_as_current_span(f"{request.method} {route}"):
        try:
            response = await call_next(request)
        except Exception:
            REQUEST_COUNT.labels(request.method, route, "500").inc()
            raise
    REQUEST_COUNT.labels(request.method, route, str(response.status_code)).inc()
    REQUEST_DURATION.labels(request.method, route).observe(perf_counter() - started)
    return response


def metrics_payload() -> bytes:
    return generate_latest()
