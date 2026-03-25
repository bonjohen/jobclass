"""NDS6: CPI-U parser, loader, and real wage computation tests."""

from pathlib import Path

import pytest

from jobclass.parse.cpi import CPI_SERIES_ID, parse_cpi

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def cpi_content():
    return (FIXTURES_DIR / "cpi_sample.txt").read_text(encoding="utf-8")


# ============================================================
# Parser tests
# ============================================================


class TestCpiParser:
    def test_filters_to_target_series(self, cpi_content):
        rows = parse_cpi(cpi_content, "test-release")
        series_ids = {r.series_id for r in rows}
        assert series_ids == {CPI_SERIES_ID}

    def test_filters_to_annual_average(self, cpi_content):
        rows = parse_cpi(cpi_content, "test-release")
        periods = {r.period for r in rows}
        assert periods == {"M13"}

    def test_extracts_annual_rows(self, cpi_content):
        rows = parse_cpi(cpi_content, "test-release")
        assert len(rows) == 4

    def test_years_correct(self, cpi_content):
        rows = parse_cpi(cpi_content, "test-release")
        years = sorted(r.year for r in rows)
        assert years == [2021, 2022, 2023, 2024]

    def test_values_numeric(self, cpi_content):
        rows = parse_cpi(cpi_content, "test-release")
        by_year = {r.year: r.value for r in rows}
        assert abs(by_year[2021] - 270.970) < 0.001
        assert abs(by_year[2022] - 292.655) < 0.001
        assert abs(by_year[2023] - 304.702) < 0.001
        assert abs(by_year[2024] - 314.690) < 0.001

    def test_metadata_populated(self, cpi_content):
        rows = parse_cpi(cpi_content, "test-release")
        for r in rows:
            assert r.source_release_id == "test-release"
            assert r.parser_version is not None

    def test_empty_content(self):
        rows = parse_cpi("", "test")
        assert rows == []

    def test_header_only(self):
        rows = parse_cpi("series_id\tyear\tperiod\tvalue\n", "test")
        assert rows == []


# ============================================================
# Loader tests
# ============================================================


class TestCpiLoader:
    def test_staging_load(self, migrated_db, cpi_content):
        from jobclass.load.cpi import load_cpi_staging

        rows = parse_cpi(cpi_content, "test-release")
        load_cpi_staging(migrated_db, rows, "test-release")
        count = migrated_db.execute("SELECT COUNT(*) FROM stage__bls__cpi").fetchone()[0]
        assert count == 4

    def test_staging_idempotent(self, migrated_db, cpi_content):
        from jobclass.load.cpi import load_cpi_staging

        rows = parse_cpi(cpi_content, "test-release")
        load_cpi_staging(migrated_db, rows, "test-release")
        load_cpi_staging(migrated_db, rows, "test-release")
        count = migrated_db.execute("SELECT COUNT(*) FROM stage__bls__cpi").fetchone()[0]
        assert count == 4

    def test_dim_price_index(self, migrated_db, cpi_content):
        from jobclass.load.cpi import load_cpi_staging, load_dim_price_index

        rows = parse_cpi(cpi_content, "test-release")
        load_cpi_staging(migrated_db, rows, "test-release")
        load_dim_price_index(migrated_db, "test-release")
        count = migrated_db.execute("SELECT COUNT(*) FROM dim_price_index").fetchone()[0]
        assert count == 1

    def test_dim_price_index_idempotent(self, migrated_db, cpi_content):
        from jobclass.load.cpi import load_cpi_staging, load_dim_price_index

        rows = parse_cpi(cpi_content, "test-release")
        load_cpi_staging(migrated_db, rows, "test-release")
        load_dim_price_index(migrated_db, "test-release")
        load_dim_price_index(migrated_db, "test-release")
        count = migrated_db.execute("SELECT COUNT(*) FROM dim_price_index").fetchone()[0]
        assert count == 1

    def test_fact_observation(self, cpi_loaded_db):
        count = cpi_loaded_db.execute("SELECT COUNT(*) FROM fact_price_index_observation").fetchone()[0]
        assert count == 4


@pytest.fixture
def cpi_loaded_db(migrated_db, cpi_content):
    """DB with CPI fully loaded through staging → dim → fact."""
    from jobclass.load.cpi import (
        load_cpi_staging,
        load_dim_price_index,
        load_fact_price_index_observation,
    )

    rows = parse_cpi(cpi_content, "test-release")
    load_cpi_staging(migrated_db, rows, "test-release")
    load_dim_price_index(migrated_db, "test-release")

    # Need dim_time_period populated so fact join works
    for year in [2021, 2022, 2023, 2024]:
        migrated_db.execute(
            """INSERT INTO dim_time_period (period_type, year, quarter, period_start_date, period_end_date)
               VALUES ('annual', ?, NULL, ?, ?)""",
            [year, f"{year}-01-01", f"{year}-12-31"],
        )

    load_fact_price_index_observation(migrated_db, "test-release")
    return migrated_db


# ============================================================
# Real wage computation tests
# ============================================================


class TestComputeRealWages:
    def test_no_cpi_returns_zero(self, migrated_db):
        from jobclass.load.timeseries import compute_real_wages, populate_derived_metrics, populate_dim_metric

        populate_dim_metric(migrated_db)
        populate_derived_metrics(migrated_db)
        result = compute_real_wages(migrated_db)
        assert result == 0

    def test_real_wages_computed(self, real_wage_db):
        count = real_wage_db.execute(
            "SELECT COUNT(*) FROM fact_derived_series WHERE derivation_method = 'cpi_deflation'"
        ).fetchone()[0]
        assert count > 0

    def test_real_wage_deflation_correct(self, real_wage_db):
        """Verify deflation formula: real = nominal × (CPI_2023 / CPI_year)."""
        # Get a sample real wage and verify against manual calculation
        row = real_wage_db.execute("""
            SELECT d.derived_value, obs.observed_value, tp.year
            FROM fact_derived_series d
            JOIN dim_metric dm ON d.metric_key = dm.metric_key
            JOIN fact_time_series_observation obs
              ON obs.metric_key = d.base_metric_key
              AND obs.occupation_key = d.occupation_key
              AND obs.geography_key = d.geography_key
              AND obs.period_key = d.period_key
            JOIN dim_time_period tp ON d.period_key = tp.period_key
            WHERE dm.metric_name = 'real_mean_annual_wage'
              AND obs.observed_value IS NOT NULL
            LIMIT 1
        """).fetchone()
        if row:
            derived_val, nominal_val, year = row
            # CPI values from fixture: 2021=270.970, 2022=292.655, 2023=304.702
            cpi_map = {2021: 270.970, 2022: 292.655, 2023: 304.702, 2024: 314.690}
            if year in cpi_map:
                expected = round(nominal_val * (304.702 / cpi_map[year]), 0)
                assert abs(derived_val - expected) <= 1  # rounding tolerance


@pytest.fixture
def real_wage_db(oews_loaded_db, cpi_content):
    """DB with OEWS + CPI + time-series + real wages computed."""
    from jobclass.load.cpi import (
        load_cpi_staging,
        load_dim_price_index,
        load_fact_price_index_observation,
    )
    from jobclass.load.timeseries import (
        compute_real_wages,
        normalize_oews_observations,
        populate_derived_metrics,
        populate_dim_metric,
        populate_dim_time_period,
    )

    # Time-series setup
    populate_dim_metric(oews_loaded_db)
    populate_derived_metrics(oews_loaded_db)
    populate_dim_time_period(oews_loaded_db)
    normalize_oews_observations(oews_loaded_db)

    # CPI — ensure dim_time_period covers CPI years
    for year in [2021, 2022, 2023, 2024]:
        existing = oews_loaded_db.execute(
            "SELECT period_key FROM dim_time_period WHERE period_type = 'annual' AND year = ?",
            [year],
        ).fetchone()
        if not existing:
            oews_loaded_db.execute(
                """INSERT INTO dim_time_period (period_type, year, quarter, period_start_date, period_end_date)
                   VALUES ('annual', ?, NULL, ?, ?)""",
                [year, f"{year}-01-01", f"{year}-12-31"],
            )

    rows = parse_cpi(cpi_content, "test-release")
    load_cpi_staging(oews_loaded_db, rows, "test-release")
    load_dim_price_index(oews_loaded_db, "test-release")
    load_fact_price_index_observation(oews_loaded_db, "test-release")

    # Compute real wages
    compute_real_wages(oews_loaded_db)

    return oews_loaded_db
