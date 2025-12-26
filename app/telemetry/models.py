from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TelemetryEvent(BaseModel):
    eventId: str = Field(..., description="Unique event identifier")
    timestampUtc: datetime = Field(..., description="Event timestamp in UTC (ISO 8601)")
    source: str = Field(..., description="Event source system")
    protocol: str = Field(..., description="Protocol used for the event")
    interactionId: str = Field(..., description="Interaction identifier")
    organization: str = Field(..., description="Submitting organization")
    qhin: str = Field(..., description="Qualified health information network")
    environment: str = Field(..., description="Deployment environment")
    status: Literal["SUCCESS", "FAILURE"] = Field(..., description="Execution status")
    durationMs: int = Field(..., ge=0, description="Execution duration in milliseconds")
    resultCount: int = Field(..., ge=0, description="Count of results returned")
    correlationId: str = Field(..., description="Correlation identifier for tracing")

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
