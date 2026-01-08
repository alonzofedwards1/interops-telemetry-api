import os
import sqlite3
from threading import Lock

from app.db.migrations import apply_migrations

DEFAULT_DB_PATH = os.environ.get("TELEMETRY_DB_PATH", "./telemetry.db")

_migrations_applied = False
_migration_lock = Lock()


def _ensure_migrations(db_path: str) -> None:
    global _migrations_applied
    if _migrations_applied:
        return
    with _migration_lock:
        if _migrations_applied:
            return
        apply_migrations(db_path)
        _migrations_applied = True


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with migrations applied."""
    _ensure_migrations(DEFAULT_DB_PATH)
    connection = sqlite3.connect(DEFAULT_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection
