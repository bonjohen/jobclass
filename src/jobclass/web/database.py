"""Read-only database connection for the website layer."""

from __future__ import annotations

import contextlib
import threading
from pathlib import Path

import duckdb

from jobclass.config.settings import get_config

# Thread-local storage for per-thread connections (production).
_local = threading.local()

# Global connection injected by tests via set_db(). Takes priority over
# thread-local connections so that TestClient workers see the fixture DB.
_test_conn: duckdb.DuckDBPyConnection | None = None

_db_path: str | None = None
_init_lock = threading.Lock()


def _resolve_db_path(db_path: str | Path | None = None) -> str:
    """Resolve and cache the database file path."""
    global _db_path
    if _db_path is not None:
        return _db_path

    with _init_lock:
        if _db_path is not None:
            return _db_path

        if db_path is None:
            cfg = get_config()
            db_path = cfg["db_path"]

        db_file = Path(db_path)
        if not db_file.exists():
            raise FileNotFoundError(
                f"Warehouse database not found at {db_file}. "
                f"Run 'jobclass-pipeline migrate && jobclass-pipeline run-all' first."
            )
        _db_path = str(db_file)
        return _db_path


def get_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Return a read-only DuckDB connection.

    In tests, returns the globally injected connection (set via set_db).
    In production, each thread gets its own connection so concurrent sync
    endpoints (FastAPI runs sync handlers in a thread pool) don't corrupt
    each other.
    """
    # Test-injected connection takes priority.
    if _test_conn is not None:
        return _test_conn

    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn

    resolved = _resolve_db_path(db_path)
    _local.conn = duckdb.connect(resolved, read_only=True)
    return _local.conn


def reset_db() -> None:
    """Close and reset all connections (for testing)."""
    global _test_conn, _db_path
    conn = getattr(_local, "conn", None)
    if conn is not None:
        with contextlib.suppress(duckdb.Error):
            conn.close()
        _local.conn = None
    _test_conn = None
    _db_path = None


def set_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Inject a connection directly (for testing).

    Uses a global so all threads (including FastAPI worker threads) see it.
    """
    global _test_conn
    _test_conn = conn
