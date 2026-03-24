"""Validations for Employment Projections pipeline."""

from __future__ import annotations

import duckdb

from jobclass.validate.framework import (
    ValidationResult,
    validate_grain_uniqueness,
    validate_min_row_count,
    validate_referential_integrity,
    validate_required_columns,
)


def validate_projections_structural(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
) -> list[ValidationResult]:
    """Run structural validations on projections staging."""
    results = []
    table = "stage__bls__employment_projections"

    results.append(
        validate_required_columns(
            conn,
            table,
            ["projection_cycle", "occupation_code", "base_year", "projection_year", "source_release_id"],
        )
    )

    results.append(
        validate_min_row_count(
            conn,
            table,
            min_rows=1,
            filter_clause="source_release_id = ?",
            params=[source_release_id],
        )
    )

    results.append(
        validate_grain_uniqueness(
            conn,
            table,
            ["projection_cycle", "occupation_code", "source_release_id"],
            filter_clause="source_release_id = ?",
            params=[source_release_id],
        )
    )

    return results


def validate_projections_occupation_mapping(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
    soc_version: str,
    max_unmapped_pct: float = 2.0,
) -> ValidationResult:
    """Verify occupation codes in projections map to dim_occupation.

    Allows up to max_unmapped_pct (default 2%) of codes to be unmapped,
    since projection data uses NEM codes that may include codes added
    after the SOC revision year.
    """
    total = conn.execute(
        "SELECT COUNT(DISTINCT occupation_code) FROM stage__bls__employment_projections WHERE source_release_id = ?",
        [source_release_id],
    ).fetchone()[0]
    orphans = conn.execute(
        """SELECT COUNT(DISTINCT s.occupation_code)
           FROM stage__bls__employment_projections s
           LEFT JOIN dim_occupation o
             ON s.occupation_code = o.soc_code AND o.soc_version = ?
           WHERE s.source_release_id = ?
             AND o.occupation_key IS NULL""",
        [soc_version, source_release_id],
    ).fetchone()[0]
    pct = (orphans / total * 100) if total > 0 else 0
    return ValidationResult(
        check_name="projections_occupation_mapping",
        passed=pct <= max_unmapped_pct,
        message=f"{orphans}/{total} unmapped codes ({pct:.1f}%)" if orphans > 0 else "All codes mapped",
    )


def validate_projections_fact_integrity(
    conn: duckdb.DuckDBPyConnection,
) -> ValidationResult:
    """Verify all occupation_key in fact_occupation_projections reference dim_occupation."""
    return validate_referential_integrity(
        conn,
        "fact_occupation_projections",
        "occupation_key",
        "dim_occupation",
        "occupation_key",
    )
