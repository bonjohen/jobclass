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


@pytest.fixture
def oews_national_content():
    """Return OEWS national sample CSV content."""
    return (FIXTURES_DIR / "oews_national_sample.csv").read_text(encoding="utf-8")


@pytest.fixture
def oews_state_content():
    """Return OEWS state sample CSV content."""
    return (FIXTURES_DIR / "oews_state_sample.csv").read_text(encoding="utf-8")


@pytest.fixture
def oews_loaded_db(migrated_db, soc_hierarchy_content, soc_definitions_content,
                   oews_national_content, oews_state_content):
    """DB with SOC + OEWS staging + warehouse fully loaded."""
    from jobclass.parse.soc import parse_soc_hierarchy, parse_soc_definitions
    from jobclass.load.soc import (load_soc_hierarchy_staging, load_soc_definitions_staging,
                                    load_dim_occupation, load_bridge_occupation_hierarchy)
    from jobclass.parse.oews import parse_oews
    from jobclass.load.oews import (load_oews_staging, load_dim_geography, load_dim_industry,
                                     load_fact_occupation_employment_wages)

    release = "2024.05"
    soc_ver = "2018"

    # SOC first
    h = parse_soc_hierarchy(soc_hierarchy_content, soc_ver)
    d = parse_soc_definitions(soc_definitions_content, soc_ver)
    load_soc_hierarchy_staging(migrated_db, h, soc_ver)
    load_soc_definitions_staging(migrated_db, d, soc_ver)
    load_dim_occupation(migrated_db, soc_ver, soc_ver)
    load_bridge_occupation_hierarchy(migrated_db, soc_ver, soc_ver)

    # OEWS
    nat = parse_oews(oews_national_content, release)
    st = parse_oews(oews_state_content, release)
    load_oews_staging(migrated_db, nat, "stage__bls__oews_national", release)
    load_oews_staging(migrated_db, st, "stage__bls__oews_state", release)
    load_dim_geography(migrated_db, release)
    load_dim_industry(migrated_db, "2022", release)
    load_fact_occupation_employment_wages(migrated_db, "oews_national", release, release, soc_ver)
    load_fact_occupation_employment_wages(migrated_db, "oews_state", release, release, soc_ver)

    return migrated_db
