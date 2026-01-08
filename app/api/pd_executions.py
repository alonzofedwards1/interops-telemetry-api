from typing import List

from fastapi import APIRouter

from app.pd.models import PdExecution, PdExecutionCount
from app.pd.store import get_pd_store

router = APIRouter(prefix="/pd-executions", tags=["pd-executions"])
store = get_pd_store()


@router.get("", response_model=List[PdExecution])
async def list_pd_executions() -> List[PdExecution]:
    return store.list_executions()


@router.get("/count", response_model=PdExecutionCount)
async def count_pd_executions() -> PdExecutionCount:
    return PdExecutionCount(count=store.count_executions())
