"""Fixtures for website tests."""

import tempfile
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from jobclass.config.database import apply_migrations
from jobclass.web.database import reset_db, set_db

MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "migrations"
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def warehouse_db():
    """Provide a DuckDB warehouse populated with sample data for web tests.

    Session-scoped: built once and shared across all web tests.
    Web tests are read-only (use TestClient for GET requests), so sharing is safe.
    """
    tmp_dir = tempfile.mkdtemp()
    db_path = Path(tmp_dir) / "web_test.duckdb"
    conn = duckdb.connect(str(db_path))
    apply_migrations(conn, migrations_dir=MIGRATIONS_DIR)

    # Load SOC
    from jobclass.load.soc import (
        load_bridge_occupation_hierarchy,
        load_dim_occupation,
        load_soc_definitions_staging,
        load_soc_hierarchy_staging,
    )
    from jobclass.parse.soc import parse_soc_definitions, parse_soc_hierarchy

    soc_ver = "2018"
    release = "2024.05"

    h_content = (FIXTURES_DIR / "soc_hierarchy_sample.csv").read_text(encoding="utf-8")
    d_content = (FIXTURES_DIR / "soc_definitions_sample.csv").read_text(encoding="utf-8")
    h = parse_soc_hierarchy(h_content, soc_ver)
    d = parse_soc_definitions(d_content, soc_ver)
    load_soc_hierarchy_staging(conn, h, soc_ver)
    load_soc_definitions_staging(conn, d, soc_ver)
    load_dim_occupation(conn, soc_ver, soc_ver)
    load_bridge_occupation_hierarchy(conn, soc_ver, soc_ver)

    # Load OEWS
    from jobclass.load.oews import (
        load_dim_geography,
        load_dim_industry,
        load_fact_occupation_employment_wages,
        load_oews_staging,
    )
    from jobclass.parse.oews import parse_oews

    nat_content = (FIXTURES_DIR / "oews_national_sample.csv").read_text(encoding="utf-8")
    st_content = (FIXTURES_DIR / "oews_state_sample.csv").read_text(encoding="utf-8")
    nat = parse_oews(nat_content, release)
    st = parse_oews(st_content, release)
    load_oews_staging(conn, nat, "stage__bls__oews_national", release)
    load_oews_staging(conn, st, "stage__bls__oews_state", release)
    load_dim_geography(conn, release)
    load_dim_industry(conn, "2022", release)
    load_fact_occupation_employment_wages(conn, "oews_national", release, release, soc_ver)
    load_fact_occupation_employment_wages(conn, "oews_state", release, release, soc_ver)

    # Load O*NET
    from jobclass.load.onet import (
        load_bridge_occupation_descriptor,
        load_bridge_occupation_education,
        load_bridge_occupation_task,
        load_bridge_occupation_technology,
        load_dim_descriptor,
        load_dim_education_requirement,
        load_dim_task,
        load_dim_technology,
        load_onet_descriptor_staging,
        load_onet_education_staging,
        load_onet_task_staging,
        load_onet_technology_staging,
    )
    from jobclass.parse.onet import (
        parse_onet_descriptors,
        parse_onet_education,
        parse_onet_tasks,
        parse_onet_technology,
    )

    onet_ver = "29.1"
    skills = parse_onet_descriptors((FIXTURES_DIR / "onet_skills_sample.txt").read_text(encoding="utf-8"), onet_ver)
    knowledge = parse_onet_descriptors(
        (FIXTURES_DIR / "onet_knowledge_sample.txt").read_text(encoding="utf-8"),
        onet_ver,
    )
    abilities = parse_onet_descriptors(
        (FIXTURES_DIR / "onet_abilities_sample.txt").read_text(encoding="utf-8"),
        onet_ver,
    )
    tasks = parse_onet_tasks((FIXTURES_DIR / "onet_tasks_sample.txt").read_text(encoding="utf-8"), onet_ver)

    load_onet_descriptor_staging(conn, skills, "stage__onet__skills", onet_ver)
    load_onet_descriptor_staging(conn, knowledge, "stage__onet__knowledge", onet_ver)
    load_onet_descriptor_staging(conn, abilities, "stage__onet__abilities", onet_ver)
    work_activities = parse_onet_descriptors(
        (FIXTURES_DIR / "onet_work_activities_sample.txt").read_text(encoding="utf-8"),
        onet_ver,
    )
    load_onet_descriptor_staging(conn, work_activities, "stage__onet__work_activities", onet_ver)
    education = parse_onet_education(
        (FIXTURES_DIR / "onet_education_sample.txt").read_text(encoding="utf-8"),
        onet_ver,
    )
    load_onet_education_staging(conn, education, onet_ver)
    technology = parse_onet_technology(
        (FIXTURES_DIR / "onet_technology_skills_sample.txt").read_text(encoding="utf-8"),
        onet_ver,
    )
    load_onet_technology_staging(conn, technology, onet_ver)
    load_onet_task_staging(conn, tasks, onet_ver)

    load_dim_descriptor(conn, "dim_skill", "skill_key", "stage__onet__skills", onet_ver)
    load_dim_descriptor(conn, "dim_knowledge", "knowledge_key", "stage__onet__knowledge", onet_ver)
    load_dim_descriptor(conn, "dim_ability", "ability_key", "stage__onet__abilities", onet_ver)
    load_dim_descriptor(conn, "dim_work_activity", "work_activity_key", "stage__onet__work_activities", onet_ver)
    load_dim_education_requirement(conn, onet_ver)
    load_dim_technology(conn, onet_ver)
    load_dim_task(conn, onet_ver)

    load_bridge_occupation_descriptor(
        conn, "bridge_occupation_skill", "dim_skill", "skill_key", "stage__onet__skills", onet_ver, onet_ver, soc_ver
    )
    load_bridge_occupation_descriptor(
        conn,
        "bridge_occupation_knowledge",
        "dim_knowledge",
        "knowledge_key",
        "stage__onet__knowledge",
        onet_ver,
        onet_ver,
        soc_ver,
    )
    load_bridge_occupation_descriptor(
        conn,
        "bridge_occupation_ability",
        "dim_ability",
        "ability_key",
        "stage__onet__abilities",
        onet_ver,
        onet_ver,
        soc_ver,
    )
    load_bridge_occupation_descriptor(
        conn,
        "bridge_occupation_work_activity",
        "dim_work_activity",
        "work_activity_key",
        "stage__onet__work_activities",
        onet_ver,
        onet_ver,
        soc_ver,
    )
    load_bridge_occupation_education(conn, onet_ver, onet_ver, soc_ver)
    load_bridge_occupation_technology(conn, onet_ver, onet_ver, soc_ver)
    load_bridge_occupation_task(conn, onet_ver, onet_ver, soc_ver)

    # Load CPI (deflator)
    from jobclass.load.cpi import load_cpi_staging, load_dim_price_index, load_fact_price_index_observation
    from jobclass.parse.cpi import parse_cpi

    cpi_content = (FIXTURES_DIR / "cpi_sample.txt").read_text(encoding="utf-8")
    cpi_rows = parse_cpi(cpi_content, release)
    load_cpi_staging(conn, cpi_rows, release)
    load_dim_price_index(conn, release)

    # Load CPI domain expansion
    from jobclass.load.cpi_domain import (
        load_bridge_cpi_area_hierarchy,
        load_bridge_cpi_member_hierarchy,
        load_bridge_cpi_member_relation,
        load_cpi_item_hierarchy_staging,
        load_cpi_series_staging,
        load_dim_cpi_area,
        load_dim_cpi_member,
        load_dim_cpi_series_variant,
    )
    from jobclass.parse.cpi_domain import parse_cpi_area, parse_cpi_item_hierarchy, parse_cpi_series

    cpi_items = parse_cpi_item_hierarchy(
        (FIXTURES_DIR / "cpi_item_sample.txt").read_text(encoding="utf-8"), release,
    )
    cpi_areas = parse_cpi_area(
        (FIXTURES_DIR / "cpi_area_sample.txt").read_text(encoding="utf-8"), release,
    )
    cpi_series = parse_cpi_series(
        (FIXTURES_DIR / "cpi_series_sample.txt").read_text(encoding="utf-8"), release,
    )
    load_cpi_item_hierarchy_staging(conn, cpi_items, release)
    load_cpi_series_staging(conn, cpi_series, release)
    load_dim_cpi_member(conn, cpi_items, release)
    load_dim_cpi_area(conn, cpi_areas, release)
    load_dim_cpi_series_variant(conn, cpi_series, release)
    load_bridge_cpi_member_hierarchy(conn, cpi_items, release)
    load_bridge_cpi_member_relation(conn, cpi_items, release)
    load_bridge_cpi_area_hierarchy(conn, cpi_areas, release)

    # Load Projections
    from jobclass.load.projections import load_fact_occupation_projections, load_projections_staging
    from jobclass.parse.projections import parse_employment_projections

    proj_content = (FIXTURES_DIR / "projections_sample.txt").read_text(encoding="utf-8")
    proj_rows = parse_employment_projections(proj_content, "2024.1", "2022-2032")
    load_projections_staging(conn, proj_rows, "2024.1")
    load_fact_occupation_projections(conn, "2024.1", soc_ver)

    # Run time-series pipeline
    from jobclass.orchestrate.timeseries_refresh import timeseries_refresh

    timeseries_refresh(conn)

    # Load CPI fact observations (needs dim_time_period from timeseries_refresh)
    # Then recompute real wages
    load_fact_price_index_observation(conn, release)
    from jobclass.load.timeseries import compute_real_wages

    compute_real_wages(conn)

    # Run manifest entry for metadata endpoint
    conn.execute("""
        INSERT INTO run_manifest (run_id, pipeline_name, dataset_name,
            source_name, source_release_id, load_status, completed_at)
        VALUES ('web-test-run', 'oews_refresh', 'oews_national', 'bls', '2024.05', 'success', CURRENT_TIMESTAMP)
    """)

    yield conn
    conn.close()


@pytest.fixture(scope="session")
def client(warehouse_db):
    """Provide a FastAPI TestClient with the warehouse injected.

    Session-scoped: shares the same app and DB connection across all web tests.
    """
    set_db(warehouse_db)
    from jobclass.web.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_db()
