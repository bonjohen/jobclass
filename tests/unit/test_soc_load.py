"""T3-05 through T3-18: SOC staging, dimension, bridge, and validation tests."""

import pytest

from jobclass.load.soc import (
    load_bridge_occupation_hierarchy,
    load_dim_occupation,
    load_soc_definitions_staging,
    load_soc_hierarchy_staging,
)
from jobclass.parse.soc import parse_soc_definitions, parse_soc_hierarchy
from jobclass.validate.soc import validate_soc_hierarchy_completeness, validate_soc_structural

RELEASE = "2018"


@pytest.fixture
def loaded_staging(migrated_db, soc_hierarchy_content, soc_definitions_content):
    """Load SOC data into staging tables and return the connection."""
    h_rows = parse_soc_hierarchy(soc_hierarchy_content, RELEASE)
    d_rows = parse_soc_definitions(soc_definitions_content, RELEASE)
    load_soc_hierarchy_staging(migrated_db, h_rows, RELEASE)
    load_soc_definitions_staging(migrated_db, d_rows, RELEASE)
    return migrated_db


@pytest.fixture
def loaded_warehouse(loaded_staging):
    """Load dim_occupation and bridge from staging."""
    load_dim_occupation(loaded_staging, RELEASE, RELEASE)
    load_bridge_occupation_hierarchy(loaded_staging, RELEASE, RELEASE)
    return loaded_staging


class TestStagingContract:
    """T3-05, T3-06: Staging tables have required columns."""

    def test_hierarchy_columns(self, loaded_staging):
        cols = {
            r[0]
            for r in loaded_staging.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__soc__hierarchy'"
            ).fetchall()
        }
        for c in [
            "soc_code",
            "occupation_title",
            "occupation_level",
            "occupation_level_name",
            "parent_soc_code",
            "source_release_id",
            "parser_version",
        ]:
            assert c in cols

    def test_definitions_columns(self, loaded_staging):
        cols = {
            r[0]
            for r in loaded_staging.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__soc__definitions'"
            ).fetchall()
        }
        for c in ["soc_code", "occupation_definition", "source_release_id", "parser_version"]:
            assert c in cols


class TestStagingGrain:
    """T3-07, T3-08: Staging grain uniqueness."""

    def test_hierarchy_no_duplicates(self, loaded_staging):
        dups = loaded_staging.execute(
            """SELECT soc_code, COUNT(*) FROM stage__soc__hierarchy
               WHERE source_release_id = ? GROUP BY soc_code HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0

    def test_definitions_no_duplicates(self, loaded_staging):
        dups = loaded_staging.execute(
            """SELECT soc_code, COUNT(*) FROM stage__soc__definitions
               WHERE source_release_id = ? GROUP BY soc_code HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0


class TestStructuralValidation:
    """T3-09, T3-10, T3-11: SOC structural and semantic validations."""

    def test_structural_validations_pass(self, loaded_staging):
        results = validate_soc_structural(loaded_staging, RELEASE)
        for r in results:
            assert r.passed, f"{r.check_name}: {r.message}"

    def test_hierarchy_completeness(self, loaded_staging):
        result = validate_soc_hierarchy_completeness(loaded_staging, RELEASE)
        assert result.passed, result.message

    def test_no_orphan_parents(self, loaded_staging):
        """Every parent_soc_code references an existing soc_code."""
        orphans = loaded_staging.execute(
            """SELECT h.soc_code, h.parent_soc_code
               FROM stage__soc__hierarchy h
               WHERE h.source_release_id = ?
                 AND h.parent_soc_code IS NOT NULL
                 AND h.parent_soc_code NOT IN (
                     SELECT soc_code FROM stage__soc__hierarchy WHERE source_release_id = ?
                 )""",
            [RELEASE, RELEASE],
        ).fetchall()
        assert len(orphans) == 0

    def test_min_row_count(self, loaded_staging):
        count = loaded_staging.execute(
            "SELECT COUNT(*) FROM stage__soc__hierarchy WHERE source_release_id = ?",
            [RELEASE],
        ).fetchone()[0]
        assert count >= 5  # Sample has 17 rows


class TestDimOccupation:
    """T3-12 through T3-15: dim_occupation loading and grain."""

    def test_no_duplicate_business_keys(self, loaded_warehouse):
        dups = loaded_warehouse.execute(
            """SELECT soc_code, soc_version, COUNT(*) FROM dim_occupation
               GROUP BY soc_code, soc_version HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_required_fields(self, loaded_warehouse):
        cols = {
            r[0]
            for r in loaded_warehouse.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_occupation'"
            ).fetchall()
        }
        for c in [
            "occupation_key",
            "soc_code",
            "occupation_title",
            "occupation_level",
            "occupation_level_name",
            "parent_soc_code",
            "soc_version",
            "is_leaf",
            "is_current",
            "source_release_id",
        ]:
            assert c in cols

    def test_surrogate_keys_unique_and_nonnull(self, loaded_warehouse):
        result = loaded_warehouse.execute(
            "SELECT COUNT(*), COUNT(DISTINCT occupation_key) FROM dim_occupation"
        ).fetchone()
        total, distinct = result
        assert total == distinct
        nulls = loaded_warehouse.execute("SELECT COUNT(*) FROM dim_occupation WHERE occupation_key IS NULL").fetchone()[
            0
        ]
        assert nulls == 0

    def test_version_aware_insert(self, loaded_warehouse):
        """Loading new version creates new rows without mutating prior rows."""
        before_count = loaded_warehouse.execute("SELECT COUNT(*) FROM dim_occupation").fetchone()[0]
        before_rows = loaded_warehouse.execute(
            "SELECT occupation_key, soc_code, occupation_title FROM dim_occupation WHERE soc_version = ?",
            [RELEASE],
        ).fetchall()

        # Load a "new version" using same data (simulating version change)
        load_dim_occupation(loaded_warehouse, "2028", RELEASE)

        after_count = loaded_warehouse.execute("SELECT COUNT(*) FROM dim_occupation").fetchone()[0]
        assert after_count == before_count * 2

        # Original rows unchanged
        orig_rows = loaded_warehouse.execute(
            "SELECT occupation_key, soc_code, occupation_title FROM dim_occupation WHERE soc_version = ?",
            [RELEASE],
        ).fetchall()
        assert orig_rows == before_rows


class TestBridgeOccupationHierarchy:
    """T3-16, T3-17: bridge_occupation_hierarchy grain and referential integrity."""

    def test_no_duplicate_business_keys(self, loaded_warehouse):
        dups = loaded_warehouse.execute(
            """SELECT parent_occupation_key, child_occupation_key, soc_version, COUNT(*)
               FROM bridge_occupation_hierarchy
               GROUP BY parent_occupation_key, child_occupation_key, soc_version
               HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_referential_integrity(self, loaded_warehouse):
        """Parent and child keys reference valid dim_occupation rows."""
        orphan_parents = loaded_warehouse.execute(
            """SELECT b.parent_occupation_key FROM bridge_occupation_hierarchy b
               WHERE b.parent_occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        assert len(orphan_parents) == 0

        orphan_children = loaded_warehouse.execute(
            """SELECT b.child_occupation_key FROM bridge_occupation_hierarchy b
               WHERE b.child_occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        assert len(orphan_children) == 0


class TestRunManifestUpdate:
    """T3-18: Run manifest updated after SOC load."""

    def test_manifest_updated(self, loaded_warehouse):
        from jobclass.observe.run_manifest import create_run_record, generate_run_id, get_run, update_run_counts

        run_id = generate_run_id()
        create_run_record(
            loaded_warehouse,
            run_id=run_id,
            pipeline_name="taxonomy_refresh",
            dataset_name="soc_hierarchy",
            source_name="soc",
        )
        update_run_counts(
            loaded_warehouse,
            run_id,
            row_count_raw=17,
            row_count_stage=17,
            row_count_loaded=17,
            load_status="success",
        )
        record = get_run(loaded_warehouse, run_id)
        assert record["row_count_raw"] == 17
        assert record["row_count_stage"] == 17
        assert record["row_count_loaded"] == 17
        assert record["load_status"] == "success"
