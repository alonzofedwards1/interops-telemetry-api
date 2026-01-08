import logging
from threading import Lock
from typing import List

from app.db.connection import get_connection
from app.pd.models import PdExecution

logger = logging.getLogger(__name__)


class PdExecutionStore:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def upsert_execution(
        self,
        request_id: str,
        started_at: str,
        completed_at: str,
        duration_ms: int,
        outcome: str,
        success: bool,
    ) -> None:
        connection = get_connection()
        try:
            connection.execute(
                """
                INSERT INTO pd_executions (
                    request_id,
                    started_at,
                    completed_at,
                    duration_ms,
                    outcome,
                    success
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    duration_ms=excluded.duration_ms,
                    outcome=excluded.outcome,
                    success=excluded.success;
                """,
                (request_id, started_at, completed_at, duration_ms, outcome, int(success)),
            )
            connection.commit()
        except Exception:
            logger.exception("Failed to upsert PD execution")
        finally:
            connection.close()

    def list_executions(self) -> List[PdExecution]:
        connection = get_connection()
        try:
            rows = connection.execute(
                """
                SELECT request_id, started_at, completed_at, duration_ms, outcome, success
                FROM pd_executions
                ORDER BY completed_at DESC
                """
            ).fetchall()
            return [
                PdExecution(
                    requestId=row["request_id"],
                    startedAt=row["started_at"],
                    completedAt=row["completed_at"],
                    durationMs=row["duration_ms"],
                    outcome=row["outcome"],
                    success=bool(row["success"]),
                )
                for row in rows
            ]
        except Exception:
            logger.exception("Failed to list PD executions")
            return []
        finally:
            connection.close()

    def count_executions(self) -> int:
        connection = get_connection()
        try:
            row = connection.execute("SELECT COUNT(*) AS count FROM pd_executions").fetchone()
            if not row:
                return 0
            return int(row["count"])
        except Exception:
            logger.exception("Failed to count PD executions")
            return 0
        finally:
            connection.close()


def get_pd_store() -> PdExecutionStore:
    return PdExecutionStore()
