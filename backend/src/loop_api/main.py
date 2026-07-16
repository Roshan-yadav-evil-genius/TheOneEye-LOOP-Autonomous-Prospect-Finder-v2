from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from loop_api.core.config import get_settings
from loop_api.http.errors import register_error_handlers
from loop_api.http.middleware.request_id import request_id_middleware
from loop_api.http.routers.admin import router as admin_router
from loop_api.http.routers.events import router as events_router
from loop_api.http.routers.forms import router as forms_router
from loop_api.http.routers.loop import router as loop_router
from loop_api.http.routers.system import router as system_router
from loop_api.observability.logging import configure_logging
from loop_api.observability.telemetry import configure_tracing, telemetry_middleware
from loop_api.persistence.database import create_schema


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await create_schema()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(json_logs=settings.env in {"staging", "production"})
    configure_tracing()
    app = FastAPI(
        title="LOOP API",
        version=settings.build_version,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(telemetry_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(system_router)
    app.include_router(forms_router)
    app.include_router(loop_router)
    app.include_router(events_router)
    app.include_router(admin_router)
    return app


app = create_app()
