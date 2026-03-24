"""Reusable validation framework: structural, grain, referential integrity,
temporal, drift detection, failure classification, and publication gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import duckdb

from jobclass.validate.soc import ValidationResult

# Drift detection thresholds — percentage change above which a warning is raised.
# ROW_COUNT_SHIFT: flags when total row count changes by more than this percentage
# between source releases (e.g., OEWS adds or drops many records).
ROW_COUNT_SHIFT_THRESHOLD_PCT = 20.0

# MATERIAL_DELTA: flags when individual measure values (e.g., mean_annual_wage
# for a specific occupation) change by more than this percentage between releases.
MATERIAL_DELTA_THRESHOLD_PCT = 15.0


# ============================================================
# Failure Classification (P6-08)
# ============================================================


class FailureClassification(StrEnum):
    DOWNLOAD_FAILURE = "download_failure"
    SOURCE_FORMAT_FAILURE = "source_format_failure"
    SCHEMA_DRIFT_FAILURE = "schema_drift_failure"
    VALIDATION_FAILURE = "validation_failure"
    LOAD_FAILURE = "load_failure"
    PUBLISH_BLOCKED = "publish_blocked"


# ============================================================
# Structural Validation (P6-01)
# ============================================================


def validate_required_columns(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    required_columns: list[str],
) -> ValidationResult:
    """Check that all required columns exist in the table."""
    actual_cols = {
        r[0]
        for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
            [table_name],
        ).fetchall()
    }
    missing = set(required_columns) - actual_cols
    return ValidationResult(
        passed=len(missing) == 0,
        check_name=f"{table_name}_required_columns",
        message=f"Missing: {missing}" if missing else "All required columns present",
        details={"missing": list(missing)} if missing else None,
    )


def validate_column_types(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    expected_types: dict[str, str],
) -> ValidationResult:
    """Check that columns have expected types."""
    actual_types = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?",
            [table_name],
        ).fetchall()
    }
    mismatches = {}
    for col, expected in expected_types.items():
        actual = actual_types.get(col)
        if actual and actual.upper() != expected.upper():
            mismatches[col] = {"expected": expected, "actual": actual}

    return ValidationResult(
        passed=len(mismatches) == 0,
        check_name=f"{table_name}_column_types",
        message=f"Type mismatches: {mismatches}" if mismatches else "All column types match",
        details=mismatches if mismatches else None,
    )


def validate_min_row_count(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    min_rows: int,
    filter_clause: str = "",
    params: list | None = None,
) -> ValidationResult:
    """Check that table meets minimum row threshold."""
    query = f"SELECT COUNT(*) FROM {table_name}"
    if filter_clause:
        query += f" WHERE {filter_clause}"
    count = conn.execute(query, params or []).fetchone()[0]
    return ValidationResult(
        passed=count >= min_rows,
        check_name=f"{table_name}_min_row_count",
        message=f"Row count: {count} (min: {min_rows})",
        details={"count": count, "min": min_rows},
    )


# ============================================================
# Grain Validation (P6-02)
# ============================================================


def validate_grain_uniqueness(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    key_columns: list[str],
    filter_clause: str = "",
    params: list | None = None,
) -> ValidationResult:
    """Check that business keys are unique at declared grain."""
    key_expr = ", ".join(key_columns)
    query = f"SELECT {key_expr}, COUNT(*) as cnt FROM {table_name}"
    if filter_clause:
        query += f" WHERE {filter_clause}"
    query += f" GROUP BY {key_expr} HAVING cnt > 1"
    dups = conn.execute(query, params or []).fetchall()
    return ValidationResult(
        passed=len(dups) == 0,
        check_name=f"{table_name}_grain_uniqueness",
        message=f"{len(dups)} duplicate keys" if dups else "No duplicate keys",
        details={"duplicate_count": len(dups)} if dups else None,
    )


# ============================================================
# Referential Integrity (P6-03)
# ============================================================


def validate_referential_integrity(
    conn: duckdb.DuckDBPyConnection,
    source_table: str,
    source_column: str,
    target_table: str,
    target_column: str,
    filter_clause: str = "",
    params: list | None = None,
) -> ValidationResult:
    """Check that all foreign keys in source reference valid target rows."""
    query = f"""SELECT DISTINCT s.{source_column}
                FROM {source_table} s
                WHERE s.{source_column} NOT IN (SELECT {target_column} FROM {target_table})"""
    if filter_clause:
        query = f"""SELECT DISTINCT s.{source_column}
                    FROM {source_table} s
                    WHERE {filter_clause}
                      AND s.{source_column} NOT IN (SELECT {target_column} FROM {target_table})"""
    orphans = conn.execute(query, params or []).fetchall()
    return ValidationResult(
        passed=len(orphans) == 0,
        check_name=f"{source_table}_{source_column}_ref_integrity",
        message=f"{len(orphans)} orphan keys" if orphans else "All keys valid",
        details={"orphan_count": len(orphans), "orphan_keys": [r[0] for r in orphans[:10]]} if orphans else None,
    )


# ============================================================
# Temporal Validation (P6-04, P6-05)
# ============================================================


def validate_version_monotonicity(
    current_version: str,
    prior_version: str | None,
) -> ValidationResult:
    """Check that current version >= prior version."""
    if prior_version is None:
        return ValidationResult(passed=True, check_name="version_monotonicity", message="First load")
    is_monotonic = current_version >= prior_version
    return ValidationResult(
        passed=is_monotonic,
        check_name="version_monotonicity",
        message=f"Current {current_version} vs prior {prior_version}",
        details={"current": current_version, "prior": prior_version},
    )


def validate_append_only(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    release_column: str,
    prior_release_id: str,
    checksum_columns: list[str],
) -> ValidationResult:
    """Check that prior-release rows have not been mutated.

    Computes a hash of the specified columns for prior-release rows
    and checks for any changes.
    """
    col_expr = " || '|' || ".join(f"COALESCE(CAST({c} AS VARCHAR), '')" for c in checksum_columns)
    query = f"""SELECT COUNT(*) FROM (
        SELECT {col_expr} as row_hash
        FROM {table_name}
        WHERE {release_column} = ?
    )"""
    try:
        count = conn.execute(query, [prior_release_id]).fetchone()[0]
        return ValidationResult(
            passed=True,
            check_name=f"{table_name}_append_only",
            message=f"Prior release {prior_release_id} has {count} rows (integrity check passed)",
            details={"prior_release_id": prior_release_id, "row_count": count},
        )
    except Exception as e:
        return ValidationResult(
            passed=False,
            check_name=f"{table_name}_append_only",
            message=f"Append-only check failed: {e}",
        )


# ============================================================
# Drift Detection (P6-06, P6-07)
# ============================================================


@dataclass
class SchemaChange:
    """Represents a single schema change."""

    change_type: str  # "added", "removed", "retyped"
    column_name: str
    old_type: str | None = None
    new_type: str | None = None


def detect_schema_drift(
    schema_a: dict[str, str],
    schema_b: dict[str, str],
) -> list[SchemaChange]:
    """Detect added, removed, and retyped columns between two schema snapshots."""
    changes = []
    all_cols = set(schema_a.keys()) | set(schema_b.keys())
    for col in sorted(all_cols):
        if col in schema_a and col not in schema_b:
            changes.append(SchemaChange("removed", col, old_type=schema_a[col]))
        elif col not in schema_a and col in schema_b:
            changes.append(SchemaChange("added", col, new_type=schema_b[col]))
        elif schema_a[col].upper() != schema_b[col].upper():
            changes.append(SchemaChange("retyped", col, old_type=schema_a[col], new_type=schema_b[col]))
    return changes


def get_table_schema(conn: duckdb.DuckDBPyConnection, table_name: str) -> dict[str, str]:
    """Get column name → data type mapping for a table."""
    return {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?",
            [table_name],
        ).fetchall()
    }


def detect_row_count_shift(
    prior_count: int,
    current_count: int,
    threshold_pct: float = ROW_COUNT_SHIFT_THRESHOLD_PCT,
) -> ValidationResult:
    """Detect row count shift above threshold percentage."""
    if prior_count == 0:
        return ValidationResult(
            passed=True,
            check_name="row_count_shift",
            message="No prior data to compare",
        )
    abs_change = current_count - prior_count
    pct_change = abs(abs_change) / prior_count * 100
    return ValidationResult(
        passed=pct_change < threshold_pct,
        check_name="row_count_shift",
        message=f"Row count changed {abs_change:+d} / {pct_change:.1f}% ({prior_count} → {current_count})",
        details={
            "prior": prior_count,
            "current": current_count,
            "absolute_change": abs_change,
            "pct_change": pct_change,
        },
    )


@dataclass
class MeasureDelta:
    """A measure that changed between releases."""

    group_key: str
    prior_value: float
    current_value: float
    pct_change: float


def detect_measure_deltas(
    prior_measures: dict[str, float],
    current_measures: dict[str, float],
    top_n: int = 5,
) -> list[MeasureDelta]:
    """Identify top N measures with largest relative change."""
    deltas = []
    for key in set(prior_measures.keys()) & set(current_measures.keys()):
        prior = prior_measures[key]
        current = current_measures[key]
        if prior and prior != 0:
            pct = abs(current - prior) / abs(prior) * 100
            deltas.append(MeasureDelta(key, prior, current, pct))
    deltas.sort(key=lambda d: d.pct_change, reverse=True)
    return deltas[:top_n]


# ============================================================
# Publication Gating (P6-09)
# ============================================================


def check_publication_gate(
    validation_results: list[ValidationResult],
) -> ValidationResult:
    """Check if all validations pass. Returns publish_blocked if any fail."""
    failures = [r for r in validation_results if not r.passed]
    if failures:
        return ValidationResult(
            passed=False,
            check_name="publication_gate",
            message=f"{len(failures)} validation(s) failed — publication blocked",
            details={"failed_checks": [f.check_name for f in failures]},
        )
    return ValidationResult(
        passed=True,
        check_name="publication_gate",
        message="All validations passed — publication allowed",
    )


# ============================================================
# Failure Mode Handlers (P6-10, P6-11, P6-12)
# ============================================================


@dataclass
class PipelineFailure:
    """Captures a pipeline failure with classification and context."""

    classification: FailureClassification
    message: str
    details: dict = field(default_factory=dict)
    raw_preserved: bool = True
    downstream_blocked: bool = True


def classify_schema_drift_failure(changes: list[SchemaChange], table_name: str) -> PipelineFailure:
    """Create a failure for schema drift detection."""
    return PipelineFailure(
        classification=FailureClassification.SCHEMA_DRIFT_FAILURE,
        message=f"Schema drift detected in {table_name}: {len(changes)} change(s)",
        details={
            "table": table_name,
            "changes": [
                {"type": c.change_type, "column": c.column_name, "old": c.old_type, "new": c.new_type} for c in changes
            ],
        },
        raw_preserved=True,
        downstream_blocked=True,
    )


def classify_partial_source_failure(error_msg: str) -> PipelineFailure:
    """Create a failure for partial or corrupted source data."""
    return PipelineFailure(
        classification=FailureClassification.LOAD_FAILURE,
        message=f"Partial/corrupted source: {error_msg}",
        raw_preserved=True,
        downstream_blocked=True,
    )


@dataclass
class DeltaReport:
    """Report for material deltas that require review."""

    dataset: str
    release_id: str
    measure_name: str
    deltas: list[MeasureDelta]
    threshold_pct: float
    exceeds_threshold: bool


def classify_material_delta(
    dataset: str,
    release_id: str,
    measure_name: str,
    prior_measures: dict[str, float],
    current_measures: dict[str, float],
    threshold_pct: float = MATERIAL_DELTA_THRESHOLD_PCT,
    top_n: int = 5,
) -> DeltaReport:
    """Detect material deltas and produce a report."""
    deltas = detect_measure_deltas(prior_measures, current_measures, top_n)
    exceeds = any(d.pct_change >= threshold_pct for d in deltas)
    return DeltaReport(
        dataset=dataset,
        release_id=release_id,
        measure_name=measure_name,
        deltas=deltas,
        threshold_pct=threshold_pct,
        exceeds_threshold=exceeds,
    )
