from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TelemetryEvent(BaseModel):
    eventId: str
    eventType: Literal["PD_EXECUTION"]
    timestamp: datetime

    source: dict

    correlation: dict

    execution: dict

    outcome: dict

    protocol: dict
