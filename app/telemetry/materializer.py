import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

from app.pd.store import get_pd_store
from app.telemetry.models import TelemetryEvent

logger = logging.getLogger(__name__)


def _parse_iso_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _normalize_success(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "success"}:
            return True
        if lowered in {"false", "0", "no", "n", "failure"}:
            return False
    return None


def _extract_request_id(event: TelemetryEvent, extra: dict) -> Optional[str]:
    if event.correlation and event.correlation.requestId:
        return event.correlation.requestId
    return extra.get("requestId") or extra.get("request_id")


def _extract_timestamps(
    event: TelemetryEvent, extra: dict, duration_ms: Optional[int]
) -> Tuple[Optional[str], Optional[str]]:
    started_value = extra.get("startedAt") or extra.get("started_at") or extra.get("startTimestamp")
    completed_value = extra.get("completedAt") or extra.get("completed_at") or extra.get("endTimestamp")

    completed_dt = _parse_iso_timestamp(completed_value) or event.timestamp
    completed_at = completed_dt.isoformat() if completed_dt else None

    started_dt = _parse_iso_timestamp(started_value)
    started_at = started_dt.isoformat() if started_dt else None

    if started_at is None and completed_dt and duration_ms is not None:
        started_dt = completed_dt - timedelta(milliseconds=duration_ms)
        started_at = started_dt.isoformat()

    return started_at, completed_at


def _extract_duration(event: TelemetryEvent, extra: dict) -> Optional[int]:
    if event.execution and event.execution.durationMs is not None:
        return int(event.execution.durationMs)
    extra_duration = extra.get("durationMs") or extra.get("duration_ms")
    if extra_duration is not None:
        try:
            return int(extra_duration)
        except (TypeError, ValueError):
            return None
    return None


def _extract_outcome(event: TelemetryEvent, extra: dict) -> Tuple[str, bool]:
    outcome_value = None
    if event.outcome and event.outcome.status:
        outcome_value = event.outcome.status
    outcome_value = outcome_value or extra.get("outcome") or extra.get("status")

    success_value = _normalize_success(extra.get("success"))
    if success_value is None and isinstance(outcome_value, str):
        success_value = outcome_value.strip().upper() == "SUCCESS"

    if success_value is None:
        success_value = False

    if isinstance(outcome_value, str) and outcome_value.strip():
        outcome = outcome_value.strip().lower()
    else:
        outcome = "success" if success_value else "failure"

    return outcome, success_value


def materialize_event(event: TelemetryEvent) -> None:
    if event.eventType.lower() != "pd.request.completed":
        return

    extra = event.model_extra or {}
    request_id = _extract_request_id(event, extra)
    if not request_id:
        logger.warning("PD execution materialization skipped: missing request_id")
        return

    duration_ms = _extract_duration(event, extra)
    started_at, completed_at = _extract_timestamps(event, extra, duration_ms)

    if duration_ms is None:
        completed_dt = _parse_iso_timestamp(completed_at) or event.timestamp
        started_dt = _parse_iso_timestamp(started_at)
        if started_dt and completed_dt:
            duration_ms = int((completed_dt - started_dt).total_seconds() * 1000)

    if duration_ms is None:
        logger.warning("PD execution materialization skipped: missing duration")
        return

    if not started_at or not completed_at:
        logger.warning("PD execution materialization skipped: missing timestamps")
        return

    outcome, success = _extract_outcome(event, extra)

    store = get_pd_store()
    store.upsert_execution(
        request_id=request_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        outcome=outcome,
        success=success,
    )
