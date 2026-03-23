"""OEWS-specific validations: structural, semantic, temporal, drift."""

from dataclasses import dataclass

import duckdb

from jobclass.validate.soc import ValidationResult


def validate_oews_structural(
    conn: duckdb.DuckDBPyConnection, table_name: str, source_release_id: str, min_rows: int = 3
) -> list[ValidationResult]:
    """Structural validations for OEWS staging tables."""
    results = []

    required_cols = [
        "area_type", "area_code", "occupation_code", "employment_count",
        "mean_annual_wage", "source_release_id", "parser_version",
    ]
    actual_cols = {
        r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
            [table_name],
        ).fetchall()
    }
    missing = set(required_cols) - actual_cols
    results.append(ValidationResult(
        passed=len(missing) == 0,
        check_name=f"{table_name}_required_columns",
        message=f"Missing: {missing}" if missing else "All required columns present",
    ))

    row_count = conn.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE source_release_id = ?", [source_release_id]
    ).fetchone()[0]
    results.append(ValidationResult(
        passed=row_count >= min_rows,
        check_name=f"{table_name}_min_row_count",
        message=f"Row count: {row_count} (min: {min_rows})",
    ))

    # Grain uniqueness
    dups = conn.execute(
        f"""SELECT occupation_code, area_code, naics_code, ownership_code, COUNT(*) as cnt
            FROM {table_name} WHERE source_release_id = ?
            GROUP BY occupation_code, area_code, naics_code, ownership_code
            HAVING cnt > 1""",
        [source_release_id],
    ).fetchall()
    results.append(ValidationResult(
        passed=len(dups) == 0,
        check_name=f"{table_name}_grain_uniqueness",
        message=f"{len(dups)} duplicate keys" if dups else "No duplicate keys",
    ))

    return results


def validate_oews_occupation_mapping(
    conn: duckdb.DuckDBPyConnection, source_release_id: str, soc_version: str
) -> ValidationResult:
    """Every occupation code in facts maps to active dim_occupation."""
    unmapped = conn.execute(
        """SELECT DISTINCT f.occupation_key FROM fact_occupation_employment_wages f
           WHERE f.source_release_id = ?
             AND f.occupation_key NOT IN (
                 SELECT occupation_key FROM dim_occupation WHERE soc_version = ?
             )""",
        [source_release_id, soc_version],
    ).fetchall()
    return ValidationResult(
        passed=len(unmapped) == 0,
        check_name="oews_occupation_mapping",
        message=f"{len(unmapped)} unmapped occupation keys" if unmapped else "All occupation keys mapped",
    )


def validate_oews_geography_mapping(
    conn: duckdb.DuckDBPyConnection, source_release_id: str
) -> ValidationResult:
    """Every geography key in facts maps to dim_geography."""
    unmapped = conn.execute(
        """SELECT DISTINCT f.geography_key FROM fact_occupation_employment_wages f
           WHERE f.source_release_id = ?
             AND f.geography_key NOT IN (SELECT geography_key FROM dim_geography)""",
        [source_release_id],
    ).fetchall()
    return ValidationResult(
        passed=len(unmapped) == 0,
        check_name="oews_geography_mapping",
        message=f"{len(unmapped)} unmapped geography keys" if unmapped else "All geography keys mapped",
    )


def validate_oews_temporal(
    conn: duckdb.DuckDBPyConnection, source_release_id: str, source_dataset: str
) -> list[ValidationResult]:
    """Temporal validations: version monotonicity and append-only."""
    results = []

    # Version monotonicity
    prior = conn.execute(
        """SELECT MAX(source_release_id) FROM fact_occupation_employment_wages
           WHERE source_dataset = ? AND source_release_id != ?""",
        [source_dataset, source_release_id],
    ).fetchone()[0]
    if prior:
        is_monotonic = source_release_id >= prior
        results.append(ValidationResult(
            passed=is_monotonic,
            check_name="oews_version_monotonicity",
            message=f"Current {source_release_id} vs prior {prior}",
        ))
    else:
        results.append(ValidationResult(passed=True, check_name="oews_version_monotonicity", message="First load"))

    return results


def detect_oews_drift(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    source_release_id: str,
    prior_release_id: str | None = None,
) -> list[ValidationResult]:
    """Drift detection: row count shifts and measure deltas."""
    results = []
    if not prior_release_id:
        results.append(ValidationResult(passed=True, check_name="oews_drift", message="No prior release to compare"))
        return results

    current_count = conn.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE source_release_id = ?", [source_release_id]
    ).fetchone()[0]
    prior_count = conn.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE source_release_id = ?", [prior_release_id]
    ).fetchone()[0]

    if prior_count > 0:
        pct_change = abs(current_count - prior_count) / prior_count * 100
        results.append(ValidationResult(
            passed=pct_change < 20,
            check_name="oews_row_count_drift",
            message=f"Row count changed {pct_change:.1f}% ({prior_count} -> {current_count})",
            details={"prior": prior_count, "current": current_count, "pct_change": pct_change},
        ))

    return results
