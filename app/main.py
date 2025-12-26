import logging

import uvicorn
from fastapi import FastAPI

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
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info",
    )
