from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from api.errors import register_error_handlers
from api.middleware.request_id import request_id_middleware
from api.routers.admin import router as admin_router
from api.routers.events import router as events_router
from api.routers.forms import router as forms_router
from api.routers.loop import router as loop_router
from api.routers.organization_chat import router as organization_chat_router
from api.routers.product_chat import router as product_chat_router
from api.routers.strategy_chat import router as strategy_chat_router
from api.routers.system import router as system_router
from api.routers.uploads import router as uploads_router
from api.routers.tool_customization import router as tool_customization_router
from observability.logging import configure_logging
from observability.telemetry import configure_tracing, telemetry_middleware
from persistence.database import create_schema
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


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
    app.include_router(organization_chat_router)
    app.include_router(product_chat_router)
    app.include_router(strategy_chat_router)
    app.include_router(uploads_router)
    app.include_router(tool_customization_router)
    
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/uploads", StaticFiles(directory="uploads"), name="uploads")
    
    return app


app = create_app()
