from typing import List

from fastapi import APIRouter

from app.db.pd_execution_repo import (
    list_pd_executions,
    materialize_pd_executions as run_materialize_pd_executions,
    summarize_pd_executions,
)
from app.models.pd_execution import PdExecution, PdExecutionSummary

router = APIRouter(prefix="/pd-executions", tags=["pd-executions"])


@router.get("", response_model=List[PdExecution])
async def get_pd_executions() -> List[PdExecution]:
    return list_pd_executions()


@router.get("/summary", response_model=PdExecutionSummary)
async def get_pd_executions_summary() -> PdExecutionSummary:
    return summarize_pd_executions()


@router.post("/materialize")
async def materialize_pd_executions() -> dict:
    materialized = run_materialize_pd_executions()
    return {"materialized": materialized}
