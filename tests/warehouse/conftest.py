"""Fixtures for warehouse validation tests.

These tests run against the real warehouse.duckdb populated by the pipeline.
They are skipped if the warehouse file does not exist.
"""

from pathlib import Path

import duckdb
import pytest

WAREHOUSE_PATH = Path(__file__).parent.parent.parent / "warehouse.duckdb"


@pytest.fixture(scope="module")
def warehouse_db():
    """Read-only connection to the real warehouse database.

    Skips the entire test module if the warehouse file doesn't exist.
    Connection is shared across all tests in a module for performance.
    """
    if not WAREHOUSE_PATH.exists():
        pytest.skip(f"Warehouse not found at {WAREHOUSE_PATH} — run 'jobclass-pipeline run-all' first")

    conn = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)
    yield conn
    conn.close()
