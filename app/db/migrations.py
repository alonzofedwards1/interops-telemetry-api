import logging
import sqlite3

logger = logging.getLogger(__name__)

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


def apply_migrations(db_path: str) -> None:
    """Ensure required tables exist in the telemetry database."""
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(CREATE_TABLE_SQL)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(pd_executions)")}
        if "request_id" in columns and "execution_id" not in columns:
            legacy_name = "pd_executions_legacy"
            logger.warning("Renaming legacy pd_executions table to %s", legacy_name)
            connection.execute(f"ALTER TABLE pd_executions RENAME TO {legacy_name}")
            connection.execute(CREATE_TABLE_SQL)
        connection.commit()
    finally:
        connection.close()
