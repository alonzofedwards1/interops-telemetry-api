import sqlite3


def apply_migrations(db_path: str) -> None:
    """Ensure required tables exist in the telemetry database."""
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pd_executions (
                request_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                outcome TEXT NOT NULL,
                success INTEGER NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()
