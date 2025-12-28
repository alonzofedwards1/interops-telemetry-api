import logging
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from app.timeline.store import build_patient_key, get_timeline_store

router = APIRouter(tags=["timeline"])
logger = logging.getLogger(__name__)
store = get_timeline_store()


@router.get("/timeline")
async def get_timeline(
    firstName: str = Query(..., description="Patient first name"),
    lastName: str = Query(..., description="Patient last name"),
    dob: date = Query(..., description="Patient date of birth"),
):
    try:
        patient_key = build_patient_key(firstName, lastName, dob.isoformat())
        events = store.get_timeline(patient_key)
        return {
            "patient": {"firstName": firstName, "lastName": lastName, "dob": dob.isoformat()},
            "events": events,
        }
    except Exception:
        logger.exception("Failed to retrieve patient timeline")
        raise HTTPException(status_code=500, detail="Unable to retrieve timeline")
