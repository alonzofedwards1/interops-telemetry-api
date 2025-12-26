import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

if __package__ is None or __package__ == "":
    root_path = Path(__file__).resolve().parent.parent
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))
    __package__ = "app"

from app.api.telemetry import router as telemetry_router
from app.config.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="InterOps Telemetry API")
app.include_router(telemetry_router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info",
    )
