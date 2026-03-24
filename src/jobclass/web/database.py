"""Read-only database connection for the website layer."""

from __future__ import annotations

import threading
from pathlib import Path

import duckdb

from jobclass.config.settings import get_config

_conn: duckdb.DuckDBPyConnection | None = None
_lock = threading.Lock()


def get_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Return a read-only DuckDB connection to the warehouse.

    Reuses a module-level connection for the lifetime of the process.
    Pass db_path explicitly in tests; otherwise reads from config.
    Thread-safe: uses a lock around connection initialization.
    """
    global _conn
    if _conn is not None:
        return _conn

    with _lock:
        # Double-check after acquiring lock
        if _conn is not None:
            return _conn

        if db_path is None:
            cfg = get_config()
            db_path = cfg["db_path"]

        db_file = Path(db_path)
        if not db_file.exists():
            raise FileNotFoundError(
                f"Warehouse database not found at {db_file}. "
                f"Run 'jobclass-pipeline migrate && jobclass-pipeline run-all' first."
            )
        _conn = duckdb.connect(str(db_path), read_only=True)
        return _conn


def reset_db() -> None:
    """Close and reset the connection (for testing)."""
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except duckdb.Error:
            pass
        _conn = None


def set_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Inject a connection directly (for testing)."""
    global _conn
    _conn = conn
