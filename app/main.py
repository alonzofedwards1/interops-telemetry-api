import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.control import router as control_router
from app.api.telemetry import router as telemetry_router
from app.auth.auth_routes import router as auth_router
from app.auth.token_routes import router as token_router
from app.auth.user_store import get_user_store
from app.config.settings import get_settings
from app.pd.pd_routes import router as pd_router
from app.timeline.timeline_routes import router as timeline_router

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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)
logger.info("Registering routers with API prefix %s", settings.api_prefix)
app.include_router(control_router, prefix=settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(pd_router, prefix=settings.api_prefix)
app.include_router(timeline_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(token_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def seed_admin_user() -> None:
    get_user_store().ensure_seed_user()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"message": "Invalid request"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing request")
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info",
    )
