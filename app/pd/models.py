from pydantic import BaseModel, ConfigDict, Field


class PdExecution(BaseModel):
    requestId: str = Field(..., description="PD request identifier")
    startedAt: str = Field(..., description="Execution start timestamp")
    completedAt: str = Field(..., description="Execution completion timestamp")
    durationMs: int = Field(..., ge=0, description="Execution duration in milliseconds")
    outcome: str = Field(..., description="Execution outcome")
    success: bool = Field(..., description="Execution success flag")

    model_config = ConfigDict(populate_by_name=True)


class PdExecutionCount(BaseModel):
    count: int = Field(..., ge=0, description="Total PD execution count")

    model_config = ConfigDict(populate_by_name=True)
