"""Read-only database connection for the website layer."""

from __future__ import annotations

from pathlib import Path

import duckdb

from jobclass.config.settings import get_config

_conn: duckdb.DuckDBPyConnection | None = None


def get_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Return a read-only DuckDB connection to the warehouse.

    Reuses a module-level connection for the lifetime of the process.
    Pass db_path explicitly in tests; otherwise reads from config.
    """
    global _conn
    if _conn is not None:
        return _conn

    if db_path is None:
        cfg = get_config()
        db_path = cfg["db_path"]

    _conn = duckdb.connect(str(db_path), read_only=True)
    return _conn


def reset_db() -> None:
    """Close and reset the connection (for testing)."""
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None


def set_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Inject a connection directly (for testing)."""
    global _conn
    _conn = conn
