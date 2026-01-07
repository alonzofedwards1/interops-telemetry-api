import logging

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.telemetry import router as telemetry_router
from app.auth.auth_routes import router as auth_router
from app.auth.token_routes import router as token_router
from app.config.settings import get_settings
from app.pd.pd_routes import router as pd_router
from app.timeline.timeline_routes import router as timeline_router
from interop_telemetry_api.telemetry.logger import log_telemetry_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


def generate_unique_operation_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    methods = ",".join(sorted(route.methods or []))
    path_fragment = route.path_format.strip("/").replace("/", "-") or "root"
    return f"{tag}-{methods}-{path_fragment}"


app = FastAPI(title="InterOps Telemetry API", generate_unique_id_function=generate_unique_operation_id)
API_PREFIX = "/api"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)
logger.info("Registering routers with API prefix %s", settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(pd_router, prefix=settings.api_prefix)
app.include_router(timeline_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(token_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/telemetry/test")
def telemetry_test(background_tasks: BackgroundTasks) -> dict:
    log_telemetry_event(
        background_tasks,
        event_type="telemetry.test",
        status="success",
        raw_payload={"ok": True},
    )
    return {"status": "logged"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info",
    )
