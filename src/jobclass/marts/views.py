"""Mart view helpers — verification and queries."""

from __future__ import annotations

import duckdb

MART_VIEWS = [
    "occupation_summary",
    "occupation_wages_by_geography",
    "occupation_skill_profile",
    "occupation_task_profile",
    "occupation_similarity_seeded",
]


def mart_exists(conn: duckdb.DuckDBPyConnection, view_name: str) -> bool:
    """Check whether a mart view exists in the database."""
    try:
        conn.execute(f"SELECT 1 FROM {view_name} LIMIT 0")
        return True
    except Exception:
        return False


def mart_row_count(conn: duckdb.DuckDBPyConnection, view_name: str) -> int:
    """Return the row count for a mart view."""
    return conn.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]


def all_marts_exist(conn: duckdb.DuckDBPyConnection) -> bool:
    """Check whether all five mart views exist."""
    return all(mart_exists(conn, v) for v in MART_VIEWS)
