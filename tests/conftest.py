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
    from jobclass.load.oews import (
        load_dim_geography,
        load_dim_industry,
        load_fact_occupation_employment_wages,
        load_oews_staging,
    )
    from jobclass.load.soc import (
        load_bridge_occupation_hierarchy,
        load_dim_occupation,
        load_soc_definitions_staging,
        load_soc_hierarchy_staging,
    )
    from jobclass.parse.oews import parse_oews
    from jobclass.parse.soc import parse_soc_definitions, parse_soc_hierarchy

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


@pytest.fixture
def onet_skills_content():
    """Return O*NET skills sample TSV content."""
    return (FIXTURES_DIR / "onet_skills_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def onet_knowledge_content():
    """Return O*NET knowledge sample TSV content."""
    return (FIXTURES_DIR / "onet_knowledge_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def onet_abilities_content():
    """Return O*NET abilities sample TSV content."""
    return (FIXTURES_DIR / "onet_abilities_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def onet_tasks_content():
    """Return O*NET tasks sample TSV content."""
    return (FIXTURES_DIR / "onet_tasks_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def onet_loaded_db(oews_loaded_db, onet_skills_content, onet_knowledge_content,
                   onet_abilities_content, onet_tasks_content):
    """DB with SOC + OEWS + O*NET staging + warehouse fully loaded."""
    from jobclass.load.onet import (
        load_bridge_occupation_descriptor,
        load_bridge_occupation_task,
        load_dim_descriptor,
        load_dim_task,
        load_onet_descriptor_staging,
        load_onet_task_staging,
    )
    from jobclass.parse.onet import parse_onet_descriptors, parse_onet_tasks

    release = "29.1"
    soc_ver = "2018"
    onet_ver = "29.1"

    # Parse
    skills = parse_onet_descriptors(onet_skills_content, release)
    knowledge = parse_onet_descriptors(onet_knowledge_content, release)
    abilities = parse_onet_descriptors(onet_abilities_content, release)
    tasks = parse_onet_tasks(onet_tasks_content, release)

    # Staging
    load_onet_descriptor_staging(oews_loaded_db, skills, "stage__onet__skills", release)
    load_onet_descriptor_staging(oews_loaded_db, knowledge, "stage__onet__knowledge", release)
    load_onet_descriptor_staging(oews_loaded_db, abilities, "stage__onet__abilities", release)
    load_onet_task_staging(oews_loaded_db, tasks, release)

    # Dimensions
    load_dim_descriptor(oews_loaded_db, "dim_skill", "skill_key", "stage__onet__skills", onet_ver)
    load_dim_descriptor(oews_loaded_db, "dim_knowledge", "knowledge_key", "stage__onet__knowledge", onet_ver)
    load_dim_descriptor(oews_loaded_db, "dim_ability", "ability_key", "stage__onet__abilities", onet_ver)
    load_dim_task(oews_loaded_db, onet_ver)

    # Bridges
    load_bridge_occupation_descriptor(
        oews_loaded_db, "bridge_occupation_skill", "dim_skill", "skill_key",
        "stage__onet__skills", onet_ver, release, soc_ver,
    )
    load_bridge_occupation_descriptor(
        oews_loaded_db, "bridge_occupation_knowledge", "dim_knowledge", "knowledge_key",
        "stage__onet__knowledge", onet_ver, release, soc_ver,
    )
    load_bridge_occupation_descriptor(
        oews_loaded_db, "bridge_occupation_ability", "dim_ability", "ability_key",
        "stage__onet__abilities", onet_ver, release, soc_ver,
    )
    load_bridge_occupation_task(oews_loaded_db, onet_ver, release, soc_ver)

    return oews_loaded_db


@pytest.fixture
def projections_content():
    """Return Employment Projections sample TSV content."""
    return (FIXTURES_DIR / "projections_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def projections_loaded_db(oews_loaded_db, projections_content):
    """DB with SOC + OEWS + projections staging + fact loaded."""
    from jobclass.load.projections import load_fact_occupation_projections, load_projections_staging
    from jobclass.parse.projections import parse_employment_projections

    release = "2024.1"
    soc_ver = "2018"
    cycle = "2022-2032"

    rows = parse_employment_projections(projections_content, release, cycle)
    load_projections_staging(oews_loaded_db, rows, release)
    load_fact_occupation_projections(oews_loaded_db, release, soc_ver)

    return oews_loaded_db
