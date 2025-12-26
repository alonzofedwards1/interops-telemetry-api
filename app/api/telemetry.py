import logging
from fastapi import APIRouter, Body, Response
from fastapi.responses import JSONResponse

from app.telemetry.store import get_store
from app.telemetry.validator import validate_event_payload

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
logger = logging.getLogger(__name__)
store = get_store()


@router.post("/events")
async def ingest_event(payload: dict = Body(...)) -> Response:
    event = validate_event_payload(payload)
    if event:
        store.add(event)
        return JSONResponse(status_code=202, content={"accepted": True})

    logger.info("Received invalid telemetry payload; event not stored")
    return JSONResponse(status_code=202, content={"accepted": False})


@router.get("/events")
async def list_events():
    return store.get_all()
