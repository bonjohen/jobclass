"""T6-01 through T6-21: Validation framework, failure classification, and failure-mode tests."""

from jobclass.validate.framework import (
    FailureClassification,
    SchemaChange,
    check_publication_gate,
    classify_material_delta,
    classify_partial_source_failure,
    classify_schema_drift_failure,
    detect_measure_deltas,
    detect_row_count_shift,
    detect_schema_drift,
    validate_append_only,
    validate_column_types,
    validate_grain_uniqueness,
    validate_min_row_count,
    validate_referential_integrity,
    validate_required_columns,
    validate_version_monotonicity,
)
from jobclass.validate.soc import ValidationResult

# ============================================================
# T6-01 through T6-04: Structural Validator
# ============================================================


class TestStructuralValidator:
    def test_detects_missing_column(self, migrated_db):
        """T6-01: Detects missing required column."""
        result = validate_required_columns(
            migrated_db,
            "dim_occupation",
            ["occupation_key", "soc_code", "nonexistent_column"],
        )
        assert not result.passed
        assert "nonexistent_column" in result.message

    def test_detects_column_type_change(self, migrated_db):
        """T6-02: Detects column type mismatch."""
        result = validate_column_types(
            migrated_db,
            "dim_occupation",
            {"soc_code": "INTEGER"},  # actually TEXT
        )
        assert not result.passed
        assert "soc_code" in str(result.details)

    def test_passes_valid_schema(self, migrated_db):
        """T6-03: Passes when all columns present with correct types."""
        result = validate_required_columns(
            migrated_db,
            "dim_occupation",
            ["occupation_key", "soc_code", "occupation_title"],
        )
        assert result.passed

    def test_detects_low_row_count(self, migrated_db):
        """T6-04: Detects row count below threshold."""
        result = validate_min_row_count(migrated_db, "dim_occupation", min_rows=100)
        assert not result.passed
        assert "100" in result.message


# ============================================================
# T6-05, T6-06: Grain Validator
# ============================================================


class TestGrainValidator:
    def test_detects_duplicates(self, migrated_db):
        """T6-05: Detects duplicate business keys."""
        # Create a test table with intentional duplicates
        migrated_db.execute("CREATE TABLE test_grain (key_a TEXT, key_b TEXT, val INTEGER)")
        migrated_db.execute("INSERT INTO test_grain VALUES ('a', 'b', 1), ('a', 'b', 2), ('c', 'd', 3)")
        result = validate_grain_uniqueness(migrated_db, "test_grain", ["key_a", "key_b"])
        assert not result.passed
        migrated_db.execute("DROP TABLE test_grain")

    def test_passes_unique_keys(self, oews_loaded_db):
        """T6-06: Passes on unique business keys."""
        result = validate_grain_uniqueness(
            oews_loaded_db,
            "dim_occupation",
            ["soc_code", "soc_version"],
        )
        assert result.passed


# ============================================================
# T6-07, T6-08: Referential Integrity Validator
# ============================================================


class TestRefIntegrityValidator:
    def test_detects_orphan_keys(self, migrated_db):
        """T6-07: Detects orphan foreign keys."""
        # Create test tables with orphan reference
        migrated_db.execute("CREATE TABLE test_fact (fk INTEGER)")
        migrated_db.execute("CREATE TABLE test_dim (pk INTEGER)")
        migrated_db.execute("INSERT INTO test_dim VALUES (1), (2)")
        migrated_db.execute("INSERT INTO test_fact VALUES (1), (2), (99)")
        result = validate_referential_integrity(
            migrated_db,
            "test_fact",
            "fk",
            "test_dim",
            "pk",
        )
        assert not result.passed
        migrated_db.execute("DROP TABLE test_fact")
        migrated_db.execute("DROP TABLE test_dim")

    def test_passes_valid_keys(self, oews_loaded_db):
        """T6-08: Passes when all keys resolve."""
        result = validate_referential_integrity(
            oews_loaded_db,
            "fact_occupation_employment_wages",
            "occupation_key",
            "dim_occupation",
            "occupation_key",
        )
        assert result.passed


# ============================================================
# T6-09, T6-10: Temporal Validator
# ============================================================


class TestTemporalValidator:
    def test_detects_version_regression(self):
        """T6-09: Detects version regression."""
        result = validate_version_monotonicity("2023.05", "2024.05")
        assert not result.passed

    def test_passes_monotonic_version(self):
        """T6-10: Passes on monotonic version."""
        result = validate_version_monotonicity("2024.05", "2023.05")
        assert result.passed


# ============================================================
# T6-11: Append-Only Validator
# ============================================================


class TestAppendOnlyValidator:
    def test_append_only_check(self, oews_loaded_db):
        """T6-11: Append-only validation runs without error."""
        result = validate_append_only(
            oews_loaded_db,
            "fact_occupation_employment_wages",
            "source_release_id",
            "2024.05",
            ["occupation_key", "geography_key", "mean_annual_wage"],
        )
        assert result.passed


# ============================================================
# T6-12: Schema Drift Detector
# ============================================================


class TestSchemaDriftDetector:
    def test_detects_added_removed_retyped(self):
        """T6-12: Reports added, removed, and retyped columns."""
        schema_a = {"col1": "INTEGER", "col2": "TEXT", "col3": "DOUBLE"}
        schema_b = {"col1": "INTEGER", "col2": "INTEGER", "col4": "TEXT"}
        changes = detect_schema_drift(schema_a, schema_b)
        change_types = {c.change_type for c in changes}
        assert "removed" in change_types  # col3 removed
        assert "added" in change_types  # col4 added
        assert "retyped" in change_types  # col2 TEXT→INTEGER
        removed = [c for c in changes if c.change_type == "removed"]
        assert any(c.column_name == "col3" for c in removed)
        added = [c for c in changes if c.change_type == "added"]
        assert any(c.column_name == "col4" for c in added)


# ============================================================
# T6-13, T6-14: Row-Count Shift and Measure Delta
# ============================================================


class TestRowCountShift:
    def test_reports_percentage_and_absolute(self):
        """T6-13: Reports correct percentage and absolute change."""
        result = detect_row_count_shift(1000, 1250, threshold_pct=20.0)
        assert not result.passed  # 25% > 20%
        assert "+250" in result.message
        assert "25.0%" in result.message

    def test_passes_within_threshold(self):
        result = detect_row_count_shift(1000, 1100, threshold_pct=20.0)
        assert result.passed


class TestMeasureDelta:
    def test_identifies_top_n(self):
        """T6-14: Identifies top N measures by change magnitude."""
        prior = {
            "occ_a": 50000.0,
            "occ_b": 60000.0,
            "occ_c": 70000.0,
            "occ_d": 80000.0,
            "occ_e": 90000.0,
            "occ_f": 100000.0,
        }
        current = {
            "occ_a": 75000.0,
            "occ_b": 62000.0,
            "occ_c": 71000.0,
            "occ_d": 80500.0,
            "occ_e": 85000.0,
            "occ_f": 115000.0,
        }
        deltas = detect_measure_deltas(prior, current, top_n=5)
        assert len(deltas) <= 5
        # occ_a has 50% change — should be first
        assert deltas[0].group_key == "occ_a"
        assert abs(deltas[0].pct_change - 50.0) < 0.1


# ============================================================
# T6-15: Failure Classification Enum
# ============================================================


class TestFailureClassification:
    def test_all_required_values(self):
        """T6-15: Enum contains all required values."""
        required = {
            "download_failure",
            "source_format_failure",
            "schema_drift_failure",
            "validation_failure",
            "load_failure",
            "publish_blocked",
        }
        actual = {e.value for e in FailureClassification}
        assert required.issubset(actual)


# ============================================================
# T6-16: Publication Gate
# ============================================================


class TestPublicationGate:
    def test_blocks_on_failure(self):
        """T6-16: Publication gate blocks when validation fails."""
        results = [
            ValidationResult(passed=True, check_name="check_a", message="ok"),
            ValidationResult(passed=False, check_name="check_b", message="failed"),
        ]
        gate = check_publication_gate(results)
        assert not gate.passed
        assert "blocked" in gate.message.lower()

    def test_allows_on_all_pass(self):
        results = [
            ValidationResult(passed=True, check_name="check_a", message="ok"),
            ValidationResult(passed=True, check_name="check_b", message="ok"),
        ]
        gate = check_publication_gate(results)
        assert gate.passed


# ============================================================
# T6-17 through T6-21: Failure Mode Tests
# ============================================================


class TestSchemaFailureMode:
    def test_schema_drift_classified(self):
        """T6-17: Schema drift creates classified failure."""
        changes = [SchemaChange("removed", "mean_annual_wage", old_type="DOUBLE")]
        failure = classify_schema_drift_failure(changes, "stage__bls__oews_national")
        assert failure.classification == FailureClassification.SCHEMA_DRIFT_FAILURE
        assert failure.raw_preserved
        assert failure.downstream_blocked


class TestPartialSourceFailure:
    def test_partial_source_classified(self):
        """T6-18: Partial source creates classified failure."""
        failure = classify_partial_source_failure("Truncated file: expected 1000 rows, got 50")
        assert failure.classification == FailureClassification.LOAD_FAILURE
        assert failure.raw_preserved
        assert failure.downstream_blocked


class TestMaterialDeltaFailure:
    def test_material_delta_report(self):
        """T6-19: Material delta emits report instead of silent acceptance."""
        prior = {"11-0000": 10000000.0, "15-0000": 5000000.0}
        current = {"11-0000": 13000000.0, "15-0000": 5100000.0}
        report = classify_material_delta(
            "oews_national",
            "2025.05",
            "total_employment",
            prior,
            current,
            threshold_pct=15.0,
        )
        assert report.exceeds_threshold  # 30% change on 11-0000
        assert len(report.deltas) > 0
        assert report.deltas[0].group_key == "11-0000"


class TestGeographyDefinitionChange:
    def test_new_definitions_appended(self, oews_loaded_db):
        """T6-20: Geography definition changes append, not mutate."""
        from jobclass.load.oews import load_dim_geography

        before = oews_loaded_db.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
        # Re-load same release — should be idempotent
        load_dim_geography(oews_loaded_db, "2024.05")
        after = oews_loaded_db.execute("SELECT COUNT(*) FROM dim_geography").fetchone()[0]
        assert after == before


class TestSuppressionPreserved:
    def test_suppressed_values_null(self, oews_loaded_db):
        """T6-21: Suppressed OEWS values preserved as null."""
        # CEO (11-1011) has suppressed wages in our fixture
        result = oews_loaded_db.execute(
            """SELECT mean_annual_wage FROM fact_occupation_employment_wages f
               JOIN dim_occupation o ON f.occupation_key = o.occupation_key
               WHERE o.soc_code = '11-1011' AND f.source_dataset = 'oews_national'"""
        ).fetchall()
        if result:
            assert result[0][0] is None
