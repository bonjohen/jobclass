"""Shared test fixtures."""

import tempfile
from pathlib import Path

import duckdb
import pytest


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory for test artifacts."""
    return tmp_path


@pytest.fixture
def db(tmp_path):
    """Provide a fresh DuckDB connection for each test."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    yield conn
    conn.close()


@pytest.fixture
def raw_root(tmp_path):
    """Provide a temporary raw storage root directory."""
    root = tmp_path / "raw"
    root.mkdir()
    return root
