"""Time-series dimension and fact loaders.

Populates dim_metric, dim_time_period, and fact_time_series_observation
from existing warehouse facts.
"""

from __future__ import annotations

import duckdb

from jobclass.observe.logging import get_logger

logger = get_logger(__name__)

# ============================================================
# Base metric definitions
# ============================================================

BASE_METRICS = [
    {
        "metric_name": "employment_count",
        "units": "persons",
        "display_format": "#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "base",
        "description": "Total employment count for an occupation in a geography",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "mean_annual_wage",
        "units": "dollars",
        "display_format": "$#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "base",
        "description": "Mean annual wage for an occupation in a geography",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "median_annual_wage",
        "units": "dollars",
        "display_format": "$#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "base",
        "description": "Median annual wage for an occupation in a geography",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "projected_employment",
        "units": "persons",
        "display_format": "#,##0",
        "comparability_constraint": "not_comparable",
        "derivation_type": "base",
        "description": "Projected future employment count from BLS projections",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "employment_change",
        "units": "persons",
        "display_format": "#,##0",
        "comparability_constraint": "not_comparable",
        "derivation_type": "base",
        "description": "Projected absolute change in employment from BLS projections",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "employment_change_pct",
        "units": "percent",
        "display_format": "#,##0.0%",
        "comparability_constraint": "not_comparable",
        "derivation_type": "base",
        "description": "Projected percent change in employment from BLS projections",
        "requires_comparable_input": False,
    },
]


def populate_dim_metric(conn: duckdb.DuckDBPyConnection) -> int:
    """Insert base metric definitions into dim_metric. Idempotent — skips existing."""
    inserted = 0
    for m in BASE_METRICS:
        existing = conn.execute(
            "SELECT metric_key FROM dim_metric WHERE metric_name = ?",
            [m["metric_name"]],
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO dim_metric
               (metric_name, units, display_format, comparability_constraint,
                derivation_type, description, requires_comparable_input)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                m["metric_name"],
                m["units"],
                m["display_format"],
                m["comparability_constraint"],
                m["derivation_type"],
                m["description"],
                m["requires_comparable_input"],
            ],
        )
        inserted += 1
    logger.info("dim_metric: inserted %d new metric(s)", inserted)
    return inserted


def populate_dim_time_period(conn: duckdb.DuckDBPyConnection) -> int:
    """Populate dim_time_period with annual periods covering all years in fact tables.

    Scans fact_occupation_employment_wages.estimate_year and
    fact_occupation_projections.base_year / projection_year.
    Idempotent — skips existing periods.
    """
    years: set[int] = set()

    # OEWS estimate years
    try:
        rows = conn.execute(
            "SELECT DISTINCT estimate_year FROM fact_occupation_employment_wages WHERE estimate_year IS NOT NULL"
        ).fetchall()
        years.update(r[0] for r in rows)
    except Exception:
        pass

    # Projection base and target years
    try:
        rows = conn.execute(
            "SELECT DISTINCT base_year FROM fact_occupation_projections "
            "WHERE base_year IS NOT NULL "
            "UNION "
            "SELECT DISTINCT projection_year FROM fact_occupation_projections "
            "WHERE projection_year IS NOT NULL"
        ).fetchall()
        years.update(r[0] for r in rows)
    except Exception:
        pass

    inserted = 0
    for year in sorted(years):
        existing = conn.execute(
            "SELECT period_key FROM dim_time_period WHERE period_type = 'annual' AND year = ?",
            [year],
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO dim_time_period (period_type, year, quarter, period_start_date, period_end_date)
               VALUES ('annual', ?, NULL, ?, ?)""",
            [year, f"{year}-01-01", f"{year}-12-31"],
        )
        inserted += 1
    logger.info("dim_time_period: inserted %d new period(s)", inserted)
    return inserted


# ============================================================
# Observation normalization
# ============================================================


def _get_metric_key(conn: duckdb.DuckDBPyConnection, metric_name: str) -> int | None:
    row = conn.execute("SELECT metric_key FROM dim_metric WHERE metric_name = ?", [metric_name]).fetchone()
    return row[0] if row else None


def _get_period_key(conn: duckdb.DuckDBPyConnection, year: int) -> int | None:
    row = conn.execute(
        "SELECT period_key FROM dim_time_period WHERE period_type = 'annual' AND year = ?",
        [year],
    ).fetchone()
    return row[0] if row else None


def normalize_oews_observations(
    conn: duckdb.DuckDBPyConnection,
    comparability_mode: str = "as_published",
    run_id: str | None = None,
) -> int:
    """Extract OEWS measures into fact_time_series_observation rows.

    Normalizes employment_count, mean_annual_wage, and median_annual_wage
    from fact_occupation_employment_wages.
    Idempotent: deletes existing rows for the same source_release_id + comparability_mode
    before re-inserting.
    """
    metrics = ["employment_count", "mean_annual_wage", "median_annual_wage"]
    total_inserted = 0

    for metric_name in metrics:
        metric_key = _get_metric_key(conn, metric_name)
        if metric_key is None:
            logger.warning("Metric %s not found in dim_metric, skipping", metric_name)
            continue

        # Delete existing for idempotency
        conn.execute(
            """DELETE FROM fact_time_series_observation
               WHERE metric_key = ? AND comparability_mode = ?""",
            [metric_key, comparability_mode],
        )

        # Insert from OEWS fact (DISTINCT avoids duplicates from broad/detailed
        # group overlap in BLS OEWS data where the same occupation appears in
        # multiple occupation_group rows with identical values)
        result = conn.execute(
            f"""INSERT INTO fact_time_series_observation
                (metric_key, occupation_key, geography_key, period_key,
                 source_release_id, comparability_mode, observed_value,
                 suppression_flag, run_id)
            SELECT DISTINCT
                ?,
                f.occupation_key,
                f.geography_key,
                tp.period_key,
                f.source_release_id,
                ?,
                f.{metric_name},
                CASE WHEN f.{metric_name} IS NULL THEN true ELSE false END,
                ?
            FROM fact_occupation_employment_wages f
            JOIN dim_time_period tp
              ON tp.period_type = 'annual' AND tp.year = f.estimate_year
            WHERE f.estimate_year IS NOT NULL""",
            [metric_key, comparability_mode, run_id],
        )
        count = result.fetchone()[0] if result.description else 0
        # Count via separate query
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_time_series_observation
               WHERE metric_key = ? AND comparability_mode = ?""",
            [metric_key, comparability_mode],
        ).fetchone()[0]
        total_inserted += count
        logger.info("Normalized %d %s observations", count, metric_name)

    return total_inserted


def normalize_projection_observations(
    conn: duckdb.DuckDBPyConnection,
    comparability_mode: str = "as_published",
    run_id: str | None = None,
) -> int:
    """Extract projection measures into fact_time_series_observation rows.

    Normalizes projected_employment, employment_change, and employment_change_pct
    from fact_occupation_projections. Uses a national geography key.
    """
    # Projections are national-level only; find national geography key
    nat_geo = conn.execute("SELECT geography_key FROM dim_geography WHERE geo_type = 'national' LIMIT 1").fetchone()
    if not nat_geo:
        logger.warning("No national geography found, skipping projection normalization")
        return 0
    nat_geo_key = nat_geo[0]

    metric_col_map = {
        "projected_employment": "employment_projected",
        "employment_change": "employment_change_abs",
        "employment_change_pct": "employment_change_pct",
    }

    total_inserted = 0
    for metric_name, col_name in metric_col_map.items():
        metric_key = _get_metric_key(conn, metric_name)
        if metric_key is None:
            logger.warning("Metric %s not found in dim_metric, skipping", metric_name)
            continue

        # Delete existing for idempotency
        conn.execute(
            """DELETE FROM fact_time_series_observation
               WHERE metric_key = ? AND comparability_mode = ?""",
            [metric_key, comparability_mode],
        )

        # Projections use projection_year as the period
        conn.execute(
            f"""INSERT INTO fact_time_series_observation
                (metric_key, occupation_key, geography_key, period_key,
                 source_release_id, comparability_mode, observed_value,
                 suppression_flag, run_id)
            SELECT
                ?,
                f.occupation_key,
                ?,
                tp.period_key,
                f.source_release_id,
                ?,
                f.{col_name},
                CASE WHEN f.{col_name} IS NULL THEN true ELSE false END,
                ?
            FROM fact_occupation_projections f
            JOIN dim_time_period tp
              ON tp.period_type = 'annual' AND tp.year = f.projection_year
            WHERE f.projection_year IS NOT NULL""",
            [metric_key, nat_geo_key, comparability_mode, run_id],
        )
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_time_series_observation
               WHERE metric_key = ? AND comparability_mode = ?""",
            [metric_key, comparability_mode],
        ).fetchone()[0]
        total_inserted += count
        logger.info("Normalized %d %s projection observations", count, metric_name)

    return total_inserted


# ============================================================
# Comparable history
# ============================================================


def build_comparable_history(conn: duckdb.DuckDBPyConnection) -> int:
    """Build comparable-history observation rows for vintages sharing the same SOC version.

    Only OEWS metrics (same_soc_version constraint) are eligible.
    Projection metrics (not_comparable) are excluded.
    Comparable rows are a copy of as_published rows where all vintages
    in the series share the same SOC version.
    """
    # Delete existing comparable rows
    conn.execute("DELETE FROM fact_time_series_observation WHERE comparability_mode = 'comparable'")

    # Insert comparable rows for metrics with same_soc_version constraint
    # Since we currently only have one SOC version (2018), all as_published OEWS rows
    # within that version are directly comparable
    conn.execute(
        """INSERT INTO fact_time_series_observation
           (metric_key, occupation_key, geography_key, period_key,
            source_release_id, comparability_mode, observed_value,
            suppression_flag, run_id)
        SELECT
            obs.metric_key,
            obs.occupation_key,
            obs.geography_key,
            obs.period_key,
            obs.source_release_id,
            'comparable',
            obs.observed_value,
            obs.suppression_flag,
            obs.run_id
        FROM fact_time_series_observation obs
        JOIN dim_metric m ON obs.metric_key = m.metric_key
        WHERE obs.comparability_mode = 'as_published'
          AND m.comparability_constraint = 'same_soc_version'"""
    )

    count = conn.execute(
        "SELECT COUNT(*) FROM fact_time_series_observation WHERE comparability_mode = 'comparable'"
    ).fetchone()[0]
    logger.info("Built %d comparable-history observations", count)
    return count


# ============================================================
# Derived series
# ============================================================

DERIVED_METRICS = [
    {
        "metric_name": "yoy_absolute_change",
        "units": "varies",
        "display_format": "#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "Year-over-year absolute change in metric value",
        "requires_comparable_input": True,
    },
    {
        "metric_name": "yoy_percent_change",
        "units": "percent",
        "display_format": "#,##0.0%",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "Year-over-year percent change in metric value",
        "requires_comparable_input": True,
    },
    {
        "metric_name": "rolling_avg_3yr",
        "units": "varies",
        "display_format": "#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "3-year rolling average of metric value",
        "requires_comparable_input": True,
    },
    {
        "metric_name": "state_vs_national_gap",
        "units": "varies",
        "display_format": "#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "State value minus national value for the same metric, occupation, and period",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "rank_delta",
        "units": "rank_change",
        "display_format": "#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "Change in occupation rank by metric within geography between periods",
        "requires_comparable_input": True,
    },
    {
        "metric_name": "real_mean_annual_wage",
        "units": "dollars",
        "display_format": "$#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "Inflation-adjusted mean annual wage (CPI-U deflated to base year)",
        "requires_comparable_input": False,
    },
    {
        "metric_name": "real_median_annual_wage",
        "units": "dollars",
        "display_format": "$#,##0",
        "comparability_constraint": "same_soc_version",
        "derivation_type": "derived",
        "description": "Inflation-adjusted median annual wage (CPI-U deflated to base year)",
        "requires_comparable_input": False,
    },
]

# Base year for CPI-U deflation (latest complete year with CPI data)
CPI_BASE_YEAR = 2023


def populate_derived_metrics(conn: duckdb.DuckDBPyConnection) -> int:
    """Register derived metric definitions in dim_metric. Idempotent."""
    inserted = 0
    for m in DERIVED_METRICS:
        existing = conn.execute(
            "SELECT metric_key FROM dim_metric WHERE metric_name = ?",
            [m["metric_name"]],
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO dim_metric
               (metric_name, units, display_format, comparability_constraint,
                derivation_type, description, requires_comparable_input)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                m["metric_name"],
                m["units"],
                m["display_format"],
                m["comparability_constraint"],
                m["derivation_type"],
                m["description"],
                m["requires_comparable_input"],
            ],
        )
        inserted += 1
    logger.info("dim_metric: inserted %d derived metric definition(s)", inserted)
    return inserted


def compute_yoy_absolute_change(
    conn: duckdb.DuckDBPyConnection,
    run_id: str | None = None,
) -> int:
    """Compute year-over-year absolute change for all comparable base metrics."""
    derived_key = _get_metric_key(conn, "yoy_absolute_change")
    if derived_key is None:
        return 0

    conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [derived_key])

    # Get all base metrics that support comparable history
    base_metrics = conn.execute(
        """SELECT metric_key, metric_name FROM dim_metric
           WHERE derivation_type = 'base'
             AND comparability_constraint = 'same_soc_version'"""
    ).fetchall()

    total = 0
    for base_key, _base_name in base_metrics:
        conn.execute(
            """INSERT INTO fact_derived_series
               (metric_key, base_metric_key, occupation_key, geography_key,
                period_key, comparability_mode, derived_value, derivation_method, run_id)
            SELECT
                ?,
                ?,
                curr.occupation_key,
                curr.geography_key,
                curr.period_key,
                curr.comparability_mode,
                curr.observed_value - prev.observed_value,
                'yoy_absolute_change',
                ?
            FROM fact_time_series_observation curr
            JOIN dim_time_period tp_curr ON curr.period_key = tp_curr.period_key
            JOIN dim_time_period tp_prev ON tp_prev.period_type = 'annual'
              AND tp_prev.year = tp_curr.year - 1
            JOIN fact_time_series_observation prev
              ON prev.metric_key = curr.metric_key
              AND prev.occupation_key = curr.occupation_key
              AND prev.geography_key = curr.geography_key
              AND prev.period_key = tp_prev.period_key
              AND prev.comparability_mode = curr.comparability_mode
            WHERE curr.metric_key = ?
              AND curr.comparability_mode = 'comparable'
              AND curr.observed_value IS NOT NULL
              AND prev.observed_value IS NOT NULL""",
            [derived_key, base_key, run_id, base_key],
        )
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_derived_series
               WHERE metric_key = ? AND base_metric_key = ?""",
            [derived_key, base_key],
        ).fetchone()[0]
        total += count

    logger.info("Computed %d yoy_absolute_change rows", total)
    return total


def compute_yoy_percent_change(
    conn: duckdb.DuckDBPyConnection,
    run_id: str | None = None,
) -> int:
    """Compute year-over-year percent change for all comparable base metrics."""
    derived_key = _get_metric_key(conn, "yoy_percent_change")
    if derived_key is None:
        return 0

    conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [derived_key])

    base_metrics = conn.execute(
        """SELECT metric_key, metric_name FROM dim_metric
           WHERE derivation_type = 'base'
             AND comparability_constraint = 'same_soc_version'"""
    ).fetchall()

    total = 0
    for base_key, _base_name in base_metrics:
        conn.execute(
            """INSERT INTO fact_derived_series
               (metric_key, base_metric_key, occupation_key, geography_key,
                period_key, comparability_mode, derived_value, derivation_method, run_id)
            SELECT
                ?,
                ?,
                curr.occupation_key,
                curr.geography_key,
                curr.period_key,
                curr.comparability_mode,
                ROUND(((curr.observed_value - prev.observed_value) / prev.observed_value) * 100, 2),
                'yoy_percent_change',
                ?
            FROM fact_time_series_observation curr
            JOIN dim_time_period tp_curr ON curr.period_key = tp_curr.period_key
            JOIN dim_time_period tp_prev ON tp_prev.period_type = 'annual'
              AND tp_prev.year = tp_curr.year - 1
            JOIN fact_time_series_observation prev
              ON prev.metric_key = curr.metric_key
              AND prev.occupation_key = curr.occupation_key
              AND prev.geography_key = curr.geography_key
              AND prev.period_key = tp_prev.period_key
              AND prev.comparability_mode = curr.comparability_mode
            WHERE curr.metric_key = ?
              AND curr.comparability_mode = 'comparable'
              AND curr.observed_value IS NOT NULL
              AND prev.observed_value IS NOT NULL
              AND prev.observed_value != 0""",
            [derived_key, base_key, run_id, base_key],
        )
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_derived_series
               WHERE metric_key = ? AND base_metric_key = ?""",
            [derived_key, base_key],
        ).fetchone()[0]
        total += count

    logger.info("Computed %d yoy_percent_change rows", total)
    return total


def compute_rolling_avg_3yr(
    conn: duckdb.DuckDBPyConnection,
    run_id: str | None = None,
) -> int:
    """Compute 3-year rolling average for all comparable base metrics.

    Only produces a value when 3 consecutive years of data exist.
    """
    derived_key = _get_metric_key(conn, "rolling_avg_3yr")
    if derived_key is None:
        return 0

    conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [derived_key])

    base_metrics = conn.execute(
        """SELECT metric_key FROM dim_metric
           WHERE derivation_type = 'base'
             AND comparability_constraint = 'same_soc_version'"""
    ).fetchall()

    total = 0
    for (base_key,) in base_metrics:
        conn.execute(
            """INSERT INTO fact_derived_series
               (metric_key, base_metric_key, occupation_key, geography_key,
                period_key, comparability_mode, derived_value, derivation_method, run_id)
            SELECT
                ?,
                ?,
                curr.occupation_key,
                curr.geography_key,
                curr.period_key,
                curr.comparability_mode,
                ROUND((p2.observed_value + p1.observed_value + curr.observed_value) / 3.0, 2),
                'rolling_avg_3yr',
                ?
            FROM fact_time_series_observation curr
            JOIN dim_time_period tp_curr ON curr.period_key = tp_curr.period_key
            JOIN dim_time_period tp_1 ON tp_1.period_type = 'annual' AND tp_1.year = tp_curr.year - 1
            JOIN dim_time_period tp_2 ON tp_2.period_type = 'annual' AND tp_2.year = tp_curr.year - 2
            JOIN fact_time_series_observation p1
              ON p1.metric_key = curr.metric_key
              AND p1.occupation_key = curr.occupation_key
              AND p1.geography_key = curr.geography_key
              AND p1.period_key = tp_1.period_key
              AND p1.comparability_mode = curr.comparability_mode
            JOIN fact_time_series_observation p2
              ON p2.metric_key = curr.metric_key
              AND p2.occupation_key = curr.occupation_key
              AND p2.geography_key = curr.geography_key
              AND p2.period_key = tp_2.period_key
              AND p2.comparability_mode = curr.comparability_mode
            WHERE curr.metric_key = ?
              AND curr.comparability_mode = 'comparable'
              AND curr.observed_value IS NOT NULL
              AND p1.observed_value IS NOT NULL
              AND p2.observed_value IS NOT NULL""",
            [derived_key, base_key, run_id, base_key],
        )
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_derived_series
               WHERE metric_key = ? AND base_metric_key = ?""",
            [derived_key, base_key],
        ).fetchone()[0]
        total += count

    logger.info("Computed %d rolling_avg_3yr rows", total)
    return total


def compute_state_vs_national_gap(
    conn: duckdb.DuckDBPyConnection,
    run_id: str | None = None,
) -> int:
    """Compute state value minus national value for the same metric, occupation, period."""
    derived_key = _get_metric_key(conn, "state_vs_national_gap")
    if derived_key is None:
        return 0

    conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [derived_key])

    base_metrics = conn.execute(
        """SELECT metric_key FROM dim_metric
           WHERE derivation_type = 'base'
             AND comparability_constraint = 'same_soc_version'"""
    ).fetchall()

    total = 0
    for (base_key,) in base_metrics:
        conn.execute(
            """INSERT INTO fact_derived_series
               (metric_key, base_metric_key, occupation_key, geography_key,
                period_key, comparability_mode, derived_value, derivation_method, run_id)
            SELECT
                ?,
                ?,
                state_obs.occupation_key,
                state_obs.geography_key,
                state_obs.period_key,
                state_obs.comparability_mode,
                state_obs.observed_value - nat_obs.observed_value,
                'state_vs_national_gap',
                ?
            FROM fact_time_series_observation state_obs
            JOIN dim_geography g ON state_obs.geography_key = g.geography_key
            JOIN dim_geography g_nat ON g_nat.geo_type = 'national'
            JOIN fact_time_series_observation nat_obs
              ON nat_obs.metric_key = state_obs.metric_key
              AND nat_obs.occupation_key = state_obs.occupation_key
              AND nat_obs.geography_key = g_nat.geography_key
              AND nat_obs.period_key = state_obs.period_key
              AND nat_obs.comparability_mode = state_obs.comparability_mode
            WHERE state_obs.metric_key = ?
              AND g.geo_type = 'state'
              AND state_obs.comparability_mode = 'as_published'
              AND state_obs.observed_value IS NOT NULL
              AND nat_obs.observed_value IS NOT NULL""",
            [derived_key, base_key, run_id, base_key],
        )
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_derived_series
               WHERE metric_key = ? AND base_metric_key = ?""",
            [derived_key, base_key],
        ).fetchone()[0]
        total += count

    logger.info("Computed %d state_vs_national_gap rows", total)
    return total


def compute_rank_delta(
    conn: duckdb.DuckDBPyConnection,
    run_id: str | None = None,
) -> int:
    """Compute rank change over time: rank occupations by metric within geography per period."""
    derived_key = _get_metric_key(conn, "rank_delta")
    if derived_key is None:
        return 0

    conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [derived_key])

    base_metrics = conn.execute(
        """SELECT metric_key FROM dim_metric
           WHERE derivation_type = 'base'
             AND comparability_constraint = 'same_soc_version'"""
    ).fetchall()

    total = 0
    for (base_key,) in base_metrics:
        conn.execute(
            """INSERT INTO fact_derived_series
               (metric_key, base_metric_key, occupation_key, geography_key,
                period_key, comparability_mode, derived_value, derivation_method, run_id)
            WITH ranked AS (
                SELECT
                    obs.occupation_key,
                    obs.geography_key,
                    obs.period_key,
                    obs.comparability_mode,
                    tp.year,
                    RANK() OVER (
                        PARTITION BY obs.geography_key, obs.period_key, obs.comparability_mode
                        ORDER BY obs.observed_value DESC
                    ) AS rnk
                FROM fact_time_series_observation obs
                JOIN dim_time_period tp ON obs.period_key = tp.period_key
                WHERE obs.metric_key = ?
                  AND obs.comparability_mode = 'comparable'
                  AND obs.observed_value IS NOT NULL
            )
            SELECT
                ?,
                ?,
                curr.occupation_key,
                curr.geography_key,
                curr.period_key,
                curr.comparability_mode,
                prev.rnk - curr.rnk,
                'rank_delta',
                ?
            FROM ranked curr
            JOIN ranked prev
              ON prev.occupation_key = curr.occupation_key
              AND prev.geography_key = curr.geography_key
              AND prev.comparability_mode = curr.comparability_mode
              AND prev.year = curr.year - 1""",
            [base_key, derived_key, base_key, run_id],
        )
        count = conn.execute(
            """SELECT COUNT(*) FROM fact_derived_series
               WHERE metric_key = ? AND base_metric_key = ?""",
            [derived_key, base_key],
        ).fetchone()[0]
        total += count

    logger.info("Computed %d rank_delta rows", total)
    return total


def compute_real_wages(
    conn: duckdb.DuckDBPyConnection,
    run_id: str | None = None,
) -> int:
    """Compute inflation-adjusted (real) wages using CPI-U deflation.

    For each nominal wage observation, computes:
        real_wage = nominal_wage × (CPI_base_year / CPI_observation_year)

    Requires fact_price_index_observation to be populated.
    """
    # Check if CPI data exists
    try:
        cpi_count = conn.execute("SELECT COUNT(*) FROM fact_price_index_observation").fetchone()[0]
    except Exception:
        cpi_count = 0

    if cpi_count == 0:
        logger.info("No CPI data available — skipping real wage computation")
        return 0

    # Get base year CPI value
    base_cpi_row = conn.execute(
        """SELECT fpi.index_value
           FROM fact_price_index_observation fpi
           JOIN dim_time_period tp ON fpi.period_key = tp.period_key
           WHERE tp.year = ?""",
        [CPI_BASE_YEAR],
    ).fetchone()

    if not base_cpi_row:
        logger.warning("No CPI data for base year %d — skipping real wages", CPI_BASE_YEAR)
        return 0

    total = 0
    # Map: (nominal_metric_name -> derived_metric_name)
    wage_pairs = [
        ("mean_annual_wage", "real_mean_annual_wage"),
        ("median_annual_wage", "real_median_annual_wage"),
    ]

    for nominal_name, real_name in wage_pairs:
        nominal_key = _get_metric_key(conn, nominal_name)
        real_key = _get_metric_key(conn, real_name)
        if nominal_key is None or real_key is None:
            continue

        # Clear existing real wage rows for this metric
        conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [real_key])

        conn.execute(
            """INSERT INTO fact_derived_series
               (metric_key, base_metric_key, occupation_key, geography_key,
                period_key, comparability_mode, derived_value, derivation_method, run_id)
            SELECT
                ?,
                ?,
                obs.occupation_key,
                obs.geography_key,
                obs.period_key,
                obs.comparability_mode,
                ROUND(obs.observed_value * (? / fpi.index_value), 0),
                'cpi_deflation',
                ?
            FROM fact_time_series_observation obs
            JOIN dim_time_period tp ON obs.period_key = tp.period_key
            JOIN fact_price_index_observation fpi ON fpi.period_key = obs.period_key
            WHERE obs.metric_key = ?
              AND obs.observed_value IS NOT NULL
              AND fpi.index_value > 0""",
            [real_key, nominal_key, base_cpi_row[0], run_id, nominal_key],
        )

        count = conn.execute(
            "SELECT COUNT(*) FROM fact_derived_series WHERE metric_key = ?",
            [real_key],
        ).fetchone()[0]
        total += count

    logger.info("Computed %d real wage rows (base year: %d)", total, CPI_BASE_YEAR)
    return total
