import logging
from typing import Optional

from pydantic import ValidationError

from .models import TelemetryEvent

logger = logging.getLogger(__name__)


def validate_event_payload(payload: dict) -> Optional[TelemetryEvent]:
    try:
        return TelemetryEvent(**payload)
    except ValidationError as exc:
        logger.warning("Telemetry payload validation failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error during telemetry validation")
    return None
