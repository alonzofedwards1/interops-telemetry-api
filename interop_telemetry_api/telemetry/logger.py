import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from fastapi import BackgroundTasks

DB_PATH = "/data/telemetry.db"
ISO_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ALLOWED_ENVIRONMENTS = {"local", "dev", "prod"}
ALLOWED_SOURCE_ENVIRONMENTS = {"api", "mirth", "external"}
ALLOWED_STATUSES = {"success", "error", "warning"}


def _normalize_timestamp(timestamp_utc: Optional[str]) -> str:
    if timestamp_utc:
        sanitized = timestamp_utc.strip()
        if sanitized.endswith("Z"):
            sanitized = sanitized[:-1] + "+00:00"
        parsed = datetime.fromisoformat(sanitized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime(ISO_UTC_FORMAT)
    return datetime.now(timezone.utc).strftime(ISO_UTC_FORMAT)


def _validate_enum(value: str, allowed: set[str], field_name: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"Invalid {field_name}: {value}. Allowed values: {allowed_values}")


def _insert_event(payload: dict) -> None:
    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO telemetry_events (
                event_id,
                event_type,
                timestamp_utc,
                source_system,
                source_channel_id,
                source_environment,
                organization,
                qhin,
                environment,
                status,
                duration_ms,
                result_count,
                correlation_id,
                correlation_request_id,
                correlation_message_id,
                protocol_standard,
                protocol_interaction_id,
                raw_payload
            ) VALUES (
                :event_id,
                :event_type,
                :timestamp_utc,
                :source_system,
                :source_channel_id,
                :source_environment,
                :organization,
                :qhin,
                :environment,
                :status,
                :duration_ms,
                :result_count,
                :correlation_id,
                :correlation_request_id,
                :correlation_message_id,
                :protocol_standard,
                :protocol_interaction_id,
                :raw_payload
            )
            """,
            payload,
        )
        connection.commit()
    finally:
        connection.close()


def log_telemetry_event(
    background_tasks: BackgroundTasks,
    *,
    event_type: str,
    status: Literal["success", "error", "warning"],
    raw_payload: Dict[str, Any],
    event_id: Optional[str] = None,
    source_system: Optional[str] = None,
    source_channel_id: Optional[str] = None,
    source_environment: Literal["api", "mirth", "external"] = "api",
    organization: Optional[str] = None,
    qhin: Optional[str] = None,
    duration_ms: Optional[int] = None,
    result_count: Optional[int] = None,
    correlation_id: Optional[str] = None,
    correlation_request_id: Optional[str] = None,
    correlation_message_id: Optional[str] = None,
    protocol_standard: Optional[str] = None,
    protocol_interaction_id: Optional[str] = None,
    timestamp_utc: Optional[str] = None,
    environment: Literal["local", "dev", "prod"] = os.getenv("APP_ENV", "dev"),
) -> None:
    _validate_enum(environment, ALLOWED_ENVIRONMENTS, "environment")
    _validate_enum(source_environment, ALLOWED_SOURCE_ENVIRONMENTS, "source_environment")
    _validate_enum(status, ALLOWED_STATUSES, "status")

    payload = {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp_utc": _normalize_timestamp(timestamp_utc),
        "source_system": source_system,
        "source_channel_id": source_channel_id,
        "source_environment": source_environment,
        "organization": organization,
        "qhin": qhin,
        "environment": environment,
        "status": status,
        "duration_ms": duration_ms,
        "result_count": result_count,
        "correlation_id": correlation_id,
        "correlation_request_id": correlation_request_id,
        "correlation_message_id": correlation_message_id,
        "protocol_standard": protocol_standard,
        "protocol_interaction_id": protocol_interaction_id,
        "raw_payload": json.dumps(raw_payload, separators=(",", ":")),
    }

    background_tasks.add_task(_insert_event, payload)
