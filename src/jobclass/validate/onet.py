"""O*NET-specific validations: structural, semantic, SOC version alignment."""

import duckdb

from jobclass.validate.soc import ValidationResult


def validate_onet_structural(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    source_release_id: str,
    min_rows: int = 3,
) -> list[ValidationResult]:
    """Structural validations for O*NET staging tables."""
    results = []

    # Required columns depend on table type
    if table_name == "stage__onet__tasks":
        required_cols = ["occupation_code", "task_id", "task", "source_release_id", "parser_version"]
        grain_cols = "occupation_code, task_id, source_release_id"
    else:
        required_cols = [
            "occupation_code", "element_id", "element_name", "scale_id",
            "data_value", "source_release_id", "parser_version",
        ]
        grain_cols = "occupation_code, element_id, scale_id, source_release_id"

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
        f"""SELECT {grain_cols}, COUNT(*) as cnt
            FROM {table_name} WHERE source_release_id = ?
            GROUP BY {grain_cols}
            HAVING cnt > 1""",
        [source_release_id],
    ).fetchall()
    results.append(ValidationResult(
        passed=len(dups) == 0,
        check_name=f"{table_name}_grain_uniqueness",
        message=f"{len(dups)} duplicate keys" if dups else "No duplicate keys",
    ))

    return results


def validate_onet_occupation_mapping(
    conn: duckdb.DuckDBPyConnection,
    staging_table: str,
    source_release_id: str,
    soc_version: str,
) -> ValidationResult:
    """Every occupation code in O*NET staging maps to active dim_occupation."""
    unmapped = conn.execute(
        f"""SELECT DISTINCT s.occupation_code
            FROM {staging_table} s
            WHERE s.source_release_id = ?
              AND s.occupation_code NOT IN (
                  SELECT soc_code FROM dim_occupation WHERE soc_version = ?
              )""",
        [source_release_id, soc_version],
    ).fetchall()
    return ValidationResult(
        passed=len(unmapped) == 0,
        check_name=f"{staging_table}_occupation_mapping",
        message=f"{len(unmapped)} unmapped codes" if unmapped else "All codes mapped",
    )


def validate_onet_soc_alignment(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
    soc_version: str,
) -> ValidationResult:
    """Check O*NET–SOC version alignment across all staging tables."""
    total_unmapped = 0
    for table in ["stage__onet__skills", "stage__onet__knowledge",
                   "stage__onet__abilities", "stage__onet__tasks"]:
        try:
            unmapped = conn.execute(
                f"""SELECT COUNT(DISTINCT occupation_code)
                    FROM {table}
                    WHERE source_release_id = ?
                      AND occupation_code NOT IN (
                          SELECT soc_code FROM dim_occupation WHERE soc_version = ?
                      )""",
                [source_release_id, soc_version],
            ).fetchone()[0]
            total_unmapped += unmapped
        except duckdb.CatalogException:
            pass  # table may not exist yet

    return ValidationResult(
        passed=total_unmapped == 0,
        check_name="onet_soc_alignment",
        message=f"{total_unmapped} unmapped codes across O*NET tables" if total_unmapped > 0
                else "All O*NET codes align with SOC",
    )
