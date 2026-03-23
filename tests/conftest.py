"""Shared test fixtures."""

from pathlib import Path

import duckdb
import pytest

from jobclass.config.database import apply_migrations

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
def migrated_db(tmp_path):
    """Provide a DuckDB connection with all migrations applied."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    apply_migrations(conn, migrations_dir=MIGRATIONS_DIR)
    yield conn
    conn.close()


@pytest.fixture
def raw_root(tmp_path):
    """Provide a temporary raw storage root directory."""
    root = tmp_path / "raw"
    root.mkdir()
    return root


@pytest.fixture
def soc_hierarchy_content():
    """Return SOC hierarchy sample CSV content."""
    return (FIXTURES_DIR / "soc_hierarchy_sample.csv").read_text(encoding="utf-8")


@pytest.fixture
def soc_definitions_content():
    """Return SOC definitions sample CSV content."""
    return (FIXTURES_DIR / "soc_definitions_sample.csv").read_text(encoding="utf-8")
