"""T4-06 through T4-31: OEWS staging, dimensions, fact, validations, idempotence tests."""


from jobclass.load.oews import (
    load_dim_geography,
    load_fact_occupation_employment_wages,
)
from jobclass.validate.oews import (
    detect_oews_drift,
    validate_oews_geography_mapping,
    validate_oews_occupation_mapping,
    validate_oews_structural,
    validate_oews_temporal,
)

RELEASE = "2024.05"
SOC_VER = "2018"


class TestOewsStagingContract:
    """T4-06, T4-07: Staging tables have required columns."""

    def test_national_columns(self, oews_loaded_db):
        cols = {r[0] for r in oews_loaded_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__bls__oews_national'"
        ).fetchall()}
        for c in ["area_type", "area_code", "occupation_code", "employment_count",
                   "mean_annual_wage", "source_release_id", "parser_version"]:
            assert c in cols

    def test_state_columns(self, oews_loaded_db):
        cols = {r[0] for r in oews_loaded_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__bls__oews_state'"
        ).fetchall()}
        for c in ["area_type", "area_code", "occupation_code", "mean_annual_wage"]:
            assert c in cols


class TestOewsStagingGrain:
    """T4-08, T4-09: Staging grain uniqueness."""

    def test_national_no_duplicates(self, oews_loaded_db):
        dups = oews_loaded_db.execute(
            """SELECT occupation_code, area_code, COUNT(*) FROM stage__bls__oews_national
               WHERE source_release_id = ?
               GROUP BY occupation_code, area_code, naics_code, ownership_code
               HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0

    def test_state_no_duplicates(self, oews_loaded_db):
        dups = oews_loaded_db.execute(
            """SELECT occupation_code, area_code, COUNT(*) FROM stage__bls__oews_state
               WHERE source_release_id = ?
               GROUP BY occupation_code, area_code, naics_code, ownership_code
               HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0


class TestOewsStagingRowCount:
    """T4-10: OEWS staging meets minimum row thresholds."""

    def test_national_min_rows(self, oews_loaded_db):
        count = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM stage__bls__oews_national WHERE source_release_id = ?", [RELEASE]
        ).fetchone()[0]
        assert count >= 3

    def test_state_min_rows(self, oews_loaded_db):
        count = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM stage__bls__oews_state WHERE source_release_id = ?", [RELEASE]
        ).fetchone()[0]
        assert count >= 3


class TestDimGeography:
    """T4-11 through T4-13: dim_geography grain, contract, append behavior."""

    def test_no_duplicate_business_keys(self, oews_loaded_db):
        dups = oews_loaded_db.execute(
            """SELECT geo_type, geo_code, source_release_id, COUNT(*) FROM dim_geography
               GROUP BY geo_type, geo_code, source_release_id HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_required_fields(self, oews_loaded_db):
        cols = {r[0] for r in oews_loaded_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_geography'"
        ).fetchall()}
        for c in ["geography_key", "geo_type", "geo_code", "geo_name", "is_current", "source_release_id"]:
            assert c in cols

    def test_append_on_change(self, oews_loaded_db):
        """New release does not mutate existing rows."""
        before = oews_loaded_db.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
        # Re-load same release = no new rows (idempotent)
        load_dim_geography(oews_loaded_db, RELEASE)
        after = oews_loaded_db.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
        assert after == before


class TestDimIndustry:
    """T4-14, T4-15: dim_industry grain and contract."""

    def test_no_duplicate_business_keys(self, oews_loaded_db):
        dups = oews_loaded_db.execute(
            """SELECT naics_code, naics_version, COUNT(*) FROM dim_industry
               GROUP BY naics_code, naics_version HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_required_fields(self, oews_loaded_db):
        cols = {r[0] for r in oews_loaded_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_industry'"
        ).fetchall()}
        for c in ["industry_key", "naics_code", "industry_title", "naics_version", "is_current"]:
            assert c in cols


class TestFactTable:
    """T4-16 through T4-22: fact grain, contract, time separation, lineage, referential integrity."""

    def test_no_duplicate_grain(self, oews_loaded_db):
        dups = oews_loaded_db.execute(
            """SELECT reference_period, geography_key, industry_key, ownership_code,
                      occupation_key, source_dataset, COUNT(*)
               FROM fact_occupation_employment_wages
               GROUP BY reference_period, geography_key, industry_key, ownership_code,
                        occupation_key, source_dataset
               HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_required_fields(self, oews_loaded_db):
        cols = {r[0] for r in oews_loaded_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'fact_occupation_employment_wages'"
        ).fetchall()}
        for c in ["fact_id", "reference_period", "geography_key", "occupation_key",
                   "source_dataset", "source_release_id", "load_timestamp"]:
            assert c in cols

    def test_release_time_separate_from_reference(self, oews_loaded_db):
        rows = oews_loaded_db.execute(
            "SELECT source_release_id, reference_period FROM fact_occupation_employment_wages LIMIT 5"
        ).fetchall()
        for release_id, ref_period in rows:
            assert release_id is not None
            assert ref_period is not None

    def test_source_dataset_non_null(self, oews_loaded_db):
        nulls = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_dataset IS NULL"
        ).fetchone()[0]
        assert nulls == 0

    def test_occupation_ref_integrity(self, oews_loaded_db):
        orphans = oews_loaded_db.execute(
            """SELECT DISTINCT f.occupation_key FROM fact_occupation_employment_wages f
               WHERE f.occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        assert len(orphans) == 0

    def test_geography_ref_integrity(self, oews_loaded_db):
        orphans = oews_loaded_db.execute(
            """SELECT DISTINCT f.geography_key FROM fact_occupation_employment_wages f
               WHERE f.geography_key NOT IN (SELECT geography_key FROM dim_geography)"""
        ).fetchall()
        assert len(orphans) == 0


class TestOewsValidations:
    """T4-23 through T4-28: Temporal and drift validations."""

    def test_structural_validations_pass(self, oews_loaded_db):
        for table in ["stage__bls__oews_national", "stage__bls__oews_state"]:
            results = validate_oews_structural(oews_loaded_db, table, RELEASE, min_rows=1)
            for r in results:
                assert r.passed, f"{r.check_name}: {r.message}"

    def test_occupation_mapping(self, oews_loaded_db):
        result = validate_oews_occupation_mapping(oews_loaded_db, RELEASE, SOC_VER)
        assert result.passed, result.message

    def test_geography_mapping(self, oews_loaded_db):
        result = validate_oews_geography_mapping(oews_loaded_db, RELEASE)
        assert result.passed, result.message

    def test_temporal_first_load(self, oews_loaded_db):
        results = validate_oews_temporal(oews_loaded_db, RELEASE, "oews_national")
        for r in results:
            assert r.passed, r.message

    def test_drift_no_prior(self, oews_loaded_db):
        results = detect_oews_drift(oews_loaded_db, "stage__bls__oews_national", RELEASE)
        for r in results:
            assert r.passed


class TestOewsIdempotence:
    """T4-29 through T4-31: Idempotent rerun tests."""

    def test_national_rerun_no_duplicates(self, oews_loaded_db):
        before = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_dataset = 'oews_national'"
        ).fetchone()[0]
        load_fact_occupation_employment_wages(oews_loaded_db, "oews_national", RELEASE, RELEASE, SOC_VER)
        after = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_dataset = 'oews_national'"
        ).fetchone()[0]
        assert after == before

    def test_state_rerun_no_duplicates(self, oews_loaded_db):
        before = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_dataset = 'oews_state'"
        ).fetchone()[0]
        load_fact_occupation_employment_wages(oews_loaded_db, "oews_state", RELEASE, RELEASE, SOC_VER)
        after = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_dataset = 'oews_state'"
        ).fetchone()[0]
        assert after == before

    def test_geography_rerun_no_duplicates(self, oews_loaded_db):
        before = oews_loaded_db.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
        load_dim_geography(oews_loaded_db, RELEASE)
        after = oews_loaded_db.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
        assert after == before
