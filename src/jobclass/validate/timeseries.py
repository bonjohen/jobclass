"""Time-series-specific validation rules (Phase TS7)."""

from __future__ import annotations

import duckdb

from jobclass.validate.soc import ValidationResult


def validate_period_ordering(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate that no time period has start_date after end_date."""
    bad = conn.execute(
        "SELECT COUNT(*) FROM dim_time_period WHERE period_start_date > period_end_date"
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_period_ordering",
        message=f"{bad} period(s) with start_date > end_date" if bad else "All periods ordered correctly",
    )


def validate_no_duplicate_periods(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate no duplicate (metric, occupation, geography, comparability_mode) within a period."""
    bad = conn.execute(
        """SELECT COUNT(*) FROM (
            SELECT metric_key, occupation_key, geography_key, period_key,
                   source_release_id, comparability_mode, COUNT(*) AS cnt
            FROM fact_time_series_observation
            GROUP BY metric_key, occupation_key, geography_key, period_key,
                     source_release_id, comparability_mode
            HAVING cnt > 1
        ) dupes"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_no_duplicate_periods",
        message=f"{bad} duplicate grain(s) found" if bad else "No duplicate grains",
    )


def validate_observation_metric_refs(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate all observation metric_keys exist in dim_metric."""
    bad = conn.execute(
        """SELECT COUNT(DISTINCT obs.metric_key)
           FROM fact_time_series_observation obs
           LEFT JOIN dim_metric m ON obs.metric_key = m.metric_key
           WHERE m.metric_key IS NULL"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_observation_metric_refs",
        message=f"{bad} orphan metric key(s)" if bad else "All metric keys valid",
    )


def validate_observation_period_refs(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate all observation period_keys exist in dim_time_period."""
    bad = conn.execute(
        """SELECT COUNT(DISTINCT obs.period_key)
           FROM fact_time_series_observation obs
           LEFT JOIN dim_time_period tp ON obs.period_key = tp.period_key
           WHERE tp.period_key IS NULL"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_observation_period_refs",
        message=f"{bad} orphan period key(s)" if bad else "All period keys valid",
    )


def validate_observation_occupation_refs(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate all observation occupation_keys exist in dim_occupation."""
    bad = conn.execute(
        """SELECT COUNT(DISTINCT obs.occupation_key)
           FROM fact_time_series_observation obs
           LEFT JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
           WHERE o.occupation_key IS NULL"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_observation_occupation_refs",
        message=f"{bad} orphan occupation key(s)" if bad else "All occupation keys valid",
    )


def validate_observation_geography_refs(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate all observation geography_keys exist in dim_geography."""
    bad = conn.execute(
        """SELECT COUNT(DISTINCT obs.geography_key)
           FROM fact_time_series_observation obs
           LEFT JOIN dim_geography g ON obs.geography_key = g.geography_key
           WHERE g.geography_key IS NULL"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_observation_geography_refs",
        message=f"{bad} orphan geography key(s)" if bad else "All geography keys valid",
    )


def validate_derived_base_metric_refs(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate no derived row references a base metric that does not exist in observations."""
    bad = conn.execute(
        """SELECT COUNT(*) FROM (
            SELECT DISTINCT d.base_metric_key
            FROM fact_derived_series d
            LEFT JOIN dim_metric m ON d.base_metric_key = m.metric_key
            WHERE m.metric_key IS NULL
        ) orphans"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_derived_base_metric_refs",
        message=f"{bad} orphan base_metric_key(s)" if bad else "All derived base metric keys valid",
    )


def validate_comparable_only_constraint(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate derived metrics flagged requires_comparable_input have no rows
    built from as-published-only series."""
    bad = conn.execute(
        """SELECT COUNT(*) FROM fact_derived_series d
           JOIN dim_metric m ON d.metric_key = m.metric_key
           WHERE m.requires_comparable_input = true
             AND d.comparability_mode != 'comparable'"""
    ).fetchone()[0]
    return ValidationResult(
        passed=bad == 0,
        check_name="ts_comparable_only_constraint",
        message=f"{bad} row(s) violate comparable-only constraint" if bad else "Comparable-only constraint satisfied",
    )


def validate_observation_derived_separation(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate no observation row has a derived metric_key and
    no derived row has a base metric_key."""
    obs_with_derived = conn.execute(
        """SELECT COUNT(*) FROM fact_time_series_observation obs
           JOIN dim_metric m ON obs.metric_key = m.metric_key
           WHERE m.derivation_type = 'derived'"""
    ).fetchone()[0]
    derived_with_base = conn.execute(
        """SELECT COUNT(*) FROM fact_derived_series d
           JOIN dim_metric m ON d.metric_key = m.metric_key
           WHERE m.derivation_type = 'base'"""
    ).fetchone()[0]
    total_bad = obs_with_derived + derived_with_base
    return ValidationResult(
        passed=total_bad == 0,
        check_name="ts_observation_derived_separation",
        message=(
            f"{obs_with_derived} obs row(s) with derived metric, "
            f"{derived_with_base} derived row(s) with base metric"
            if total_bad else "Clean separation between observations and derived series"
        ),
    )


def validate_comparable_subset(conn: duckdb.DuckDBPyConnection) -> ValidationResult:
    """Validate comparable-mode count <= as-published count (subset relationship)."""
    comparable = conn.execute(
        "SELECT COUNT(*) FROM fact_time_series_observation WHERE comparability_mode = 'comparable'"
    ).fetchone()[0]
    as_published = conn.execute(
        "SELECT COUNT(*) FROM fact_time_series_observation WHERE comparability_mode = 'as_published'"
    ).fetchone()[0]
    return ValidationResult(
        passed=comparable <= as_published,
        check_name="ts_comparable_subset",
        message=(
            f"comparable ({comparable}) > as_published ({as_published})"
            if comparable > as_published
            else f"comparable ({comparable}) <= as_published ({as_published})"
        ),
    )


def run_all_timeseries_validations(conn: duckdb.DuckDBPyConnection) -> list[ValidationResult]:
    """Run all time-series validation checks."""
    return [
        validate_period_ordering(conn),
        validate_no_duplicate_periods(conn),
        validate_observation_metric_refs(conn),
        validate_observation_period_refs(conn),
        validate_observation_occupation_refs(conn),
        validate_observation_geography_refs(conn),
        validate_derived_base_metric_refs(conn),
        validate_comparable_only_constraint(conn),
        validate_observation_derived_separation(conn),
        validate_comparable_subset(conn),
    ]
