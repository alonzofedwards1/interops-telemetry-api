from pydantic import BaseModel, ConfigDict, Field


class PdExecution(BaseModel):
    executionId: str = Field(..., description="Execution identifier")
    startedAt: str = Field(..., description="Execution start timestamp (ISO 8601)")
    completedAt: str = Field(..., description="Execution completion timestamp (ISO 8601)")
    durationMs: int = Field(..., ge=0, description="Execution duration in milliseconds")
    status: str = Field(..., description="Execution status (success or failure)")
    requestCount: int = Field(..., ge=0, description="Total requests processed")

    model_config = ConfigDict(populate_by_name=True)


class PdExecutionSummary(BaseModel):
    totalExecutions: int = Field(..., ge=0, description="Total executions")
    successCount: int = Field(..., ge=0, description="Total successful executions")
    failureCount: int = Field(..., ge=0, description="Total failed executions")
    averageDurationMs: int = Field(..., ge=0, description="Average execution duration in milliseconds")

    model_config = ConfigDict(populate_by_name=True)
