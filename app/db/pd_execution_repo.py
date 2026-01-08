import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from app.models.pd_execution import PdExecution, PdExecutionSummary

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("TELEMETRY_DB_PATH", "./telemetry.db")
TABLE_NAME = "pd_executions"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pd_executions (
    execution_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    request_count INTEGER NOT NULL
);
"""


def _get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(CREATE_TABLE_SQL)
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(pd_executions)")}
    required = {"execution_id", "started_at", "completed_at", "duration_ms", "status", "request_count"}
    if required.issubset(columns):
        return

    if "request_id" in columns and "execution_id" not in columns:
        legacy_name = "pd_executions_legacy"
        logger.warning("Renaming legacy pd_executions table to %s", legacy_name)
        connection.execute(f"ALTER TABLE pd_executions RENAME TO {legacy_name}")
        connection.execute(CREATE_TABLE_SQL)
        connection.commit()
        return

    missing = required - columns
    if missing:
        logger.warning("PD executions table missing columns %s", sorted(missing))


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_status(value: Optional[str]) -> str:
    if not value:
        return "failure"
    lowered = value.strip().lower()
    if lowered in {"success", "succeeded", "ok", "true"}:
        return "success"
    if lowered in {"failure", "failed", "error", "false"}:
        return "failure"
    if value.strip().upper() == "SUCCESS":
        return "success"
    return "failure"


def _extract_execution_id(payload: dict, row: sqlite3.Row) -> Optional[str]:
    return (
        row.get("correlation_request_id")
        or payload.get("executionId")
        or payload.get("execution_id")
        or payload.get("requestId")
        or payload.get("request_id")
        or row.get("event_id")
    )


def _extract_payload(row: sqlite3.Row) -> dict:
    raw_payload = row.get("raw_payload")
    if not raw_payload:
        return {}
    try:
        return json.loads(raw_payload)
    except json.JSONDecodeError:
        logger.warning("Failed to parse telemetry raw_payload for event_id=%s", row.get("event_id"))
        return {}


def _extract_execution(row: sqlite3.Row) -> Optional[PdExecution]:
    payload = _extract_payload(row)
    execution_id = _extract_execution_id(payload, row)
    if not execution_id:
        return None

    duration_ms = row.get("duration_ms")
    if duration_ms is None:
        duration_ms = payload.get("durationMs") or payload.get("duration_ms")
    try:
        duration_ms = int(duration_ms) if duration_ms is not None else None
    except (TypeError, ValueError):
        duration_ms = None

    completed_at = payload.get("completedAt") or payload.get("completed_at") or row.get("timestamp_utc")
    started_at = payload.get("startedAt") or payload.get("started_at")

    completed_dt = _parse_iso(completed_at) if completed_at else None
    started_dt = _parse_iso(started_at) if started_at else None

    if started_dt is None and completed_dt and duration_ms is not None:
        started_dt = completed_dt - timedelta(milliseconds=duration_ms)
        started_at = started_dt.isoformat()

    if completed_dt and not completed_at:
        completed_at = completed_dt.isoformat()

    if not completed_at or not started_at or duration_ms is None:
        return None

    status = payload.get("status") or payload.get("outcome") or row.get("status")
    status = _normalize_status(status)

    request_count = row.get("result_count")
    if request_count is None:
        request_count = payload.get("requestCount") or payload.get("resultCount")
    try:
        request_count = int(request_count) if request_count is not None else 1
    except (TypeError, ValueError):
        request_count = 1

    return PdExecution(
        executionId=str(execution_id),
        startedAt=started_at,
        completedAt=completed_at,
        durationMs=duration_ms,
        status=status,
        requestCount=request_count,
    )


def list_pd_executions() -> List[PdExecution]:
    connection = _get_connection()
    try:
        _ensure_schema(connection)
        rows = connection.execute(
            """
            SELECT execution_id, started_at, completed_at, duration_ms, status, request_count
            FROM pd_executions
            ORDER BY completed_at DESC
            """
        ).fetchall()
        return [
            PdExecution(
                executionId=row["execution_id"],
                startedAt=row["started_at"],
                completedAt=row["completed_at"],
                durationMs=row["duration_ms"],
                status=row["status"],
                requestCount=row["request_count"],
            )
            for row in rows
        ]
    finally:
        connection.close()


def summarize_pd_executions() -> PdExecutionSummary:
    connection = _get_connection()
    try:
        _ensure_schema(connection)
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) AS failure_count,
                AVG(duration_ms) AS avg_duration
            FROM pd_executions
            """
        ).fetchone()
        total = int(row["total"] or 0)
        success_count = int(row["success_count"] or 0)
        failure_count = int(row["failure_count"] or 0)
        avg_duration = int(row["avg_duration"] or 0)
        return PdExecutionSummary(
            totalExecutions=total,
            successCount=success_count,
            failureCount=failure_count,
            averageDurationMs=avg_duration,
        )
    finally:
        connection.close()


def _telemetry_rows(connection: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            event_id,
            event_type,
            timestamp_utc,
            status,
            duration_ms,
            result_count,
            correlation_request_id,
            raw_payload
        FROM telemetry_events
        WHERE lower(event_type) = 'pd.request.completed'
        """
    ).fetchall()


def materialize_pd_executions() -> int:
    connection = _get_connection()
    try:
        _ensure_schema(connection)
        materialized = 0
        rows = _telemetry_rows(connection)
        for row in rows:
            execution = _extract_execution(row)
            if not execution:
                logger.warning("Skipping telemetry event %s: missing execution fields", row.get("event_id"))
                continue
            connection.execute(
                """
                INSERT INTO pd_executions (
                    execution_id,
                    started_at,
                    completed_at,
                    duration_ms,
                    status,
                    request_count
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(execution_id) DO UPDATE SET
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    duration_ms=excluded.duration_ms,
                    status=excluded.status,
                    request_count=excluded.request_count
                """,
                (
                    execution.executionId,
                    execution.startedAt,
                    execution.completedAt,
                    execution.durationMs,
                    execution.status,
                    execution.requestCount,
                ),
            )
            materialized += 1
        connection.commit()
        return materialized
    except sqlite3.OperationalError:
        logger.exception("Failed to materialize PD executions from telemetry events")
        return 0
    finally:
        connection.close()
