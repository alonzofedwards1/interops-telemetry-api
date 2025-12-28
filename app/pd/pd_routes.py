import logging
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth.openemr_auth import get_openemr_auth_manager
from app.config.settings import get_settings
from app.telemetry.models import (
    CorrelationInfo,
    OutcomeInfo,
    ProtocolInfo,
    SourceInfo,
    TelemetryEvent,
)
from app.telemetry.store import get_store
from app.timeline.store import build_patient_key, get_timeline_store

router = APIRouter(prefix="/pd", tags=["patient-discovery"])
logger = logging.getLogger(__name__)
telemetry_store = get_store()
timeline_store = get_timeline_store()


class Demographics(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    dob: date

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class PDSearchRequest(BaseModel):
    request_id: Optional[str] = Field(None, alias="request_id")
    demographics: Demographics

    model_config = ConfigDict(populate_by_name=True)


@router.post("/search")
async def pd_search(request: PDSearchRequest):
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - environment guardrail
        logger.error("httpx is required to submit PD requests; install from requirements.txt")
        raise HTTPException(status_code=500, detail="httpx dependency missing") from exc

    settings = get_settings()
    if not settings.mirth_pd_endpoint_url:
        logger.error("Mirth PD endpoint URL is not configured")
        raise HTTPException(status_code=500, detail="Mirth PD endpoint not configured")

    correlation_id = request.request_id or str(uuid4())
    payload = {
        "request_id": request.request_id,
        "correlation_id": correlation_id,
        "demographics": {
            "firstName": request.demographics.firstName,
            "lastName": request.demographics.lastName,
            "dob": request.demographics.dob.isoformat(),
        },
    }

    manager = get_openemr_auth_manager()

    try:
        await manager.get_access_token()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to obtain OpenEMR access token before PD search")
        raise HTTPException(status_code=502, detail="Unable to obtain OpenEMR access token")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(settings.mirth_pd_endpoint_url, json=payload)
    except Exception:
        logger.exception("Failed to invoke Mirth PD endpoint")
        raise HTTPException(status_code=502, detail="Unable to submit PD request to Mirth")

    now = datetime.utcnow()
    telemetry_event = TelemetryEvent(
        eventId=str(uuid4()),
        eventType="PD_SEARCH_REQUEST",
        timestamp=now,
        source=SourceInfo(system="interop-ui"),
        correlation=CorrelationInfo(requestId=correlation_id),
        protocol=ProtocolInfo(standard="PD"),
        outcome=OutcomeInfo(status="REQUESTED"),
        destination="mirth",
    )

    telemetry_store.add(telemetry_event)

    patient_key = build_patient_key(
        request.demographics.firstName,
        request.demographics.lastName,
        request.demographics.dob.isoformat(),
    )
    timeline_store.add_event(
        patient_key,
        {
            "timestamp": now.isoformat(),
            "type": "PD_REQUEST",
            "status": "REQUESTED",
            "details": {
                "correlation_id": correlation_id,
                "request_id": request.request_id,
            },
        },
    )

    return {"status": "submitted", "correlation_id": correlation_id}
