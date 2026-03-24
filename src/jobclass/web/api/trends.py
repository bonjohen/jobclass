"""Time-series trend API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query

from jobclass.web.database import get_db

router = APIRouter(prefix="/api", tags=["trends"])

_SOC_CODE_RE = re.compile(r"^\d{2}-\d{4}$")
_VALID_METRICS = {
    "employment_count",
    "mean_annual_wage",
    "median_annual_wage",
    "projected_employment",
    "employment_change",
    "employment_change_pct",
}


def _table_exists(conn, table_name: str) -> bool:
    try:
        conn.execute(f"SELECT 1 FROM {table_name} LIMIT 0")
        return True
    except Exception:
        return False


@router.get("/trends/compare/occupations")
def compare_occupations(
    soc_codes: str = Query(..., description="Comma-separated SOC codes"),
    metric: str = Query("employment_count"),
    geo_type: str = Query("national"),
    comparability_mode: str = Query("as_published"),
) -> dict:
    """Compare a metric across multiple occupations over time."""
    codes = [c.strip() for c in soc_codes.split(",") if c.strip()]
    if not codes or len(codes) > 10:
        raise HTTPException(status_code=400, detail="Provide 1-10 comma-separated SOC codes")

    conn = get_db()

    if not _table_exists(conn, "fact_time_series_observation"):
        return {"metric": metric, "occupations": []}

    results = []
    for code in codes:
        if not _SOC_CODE_RE.match(code):
            continue
        rows = conn.execute(
            """
            SELECT tp.year, obs.observed_value, o.occupation_title
            FROM fact_time_series_observation obs
            JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
            JOIN dim_metric m ON obs.metric_key = m.metric_key
            JOIN dim_geography g ON obs.geography_key = g.geography_key
            JOIN dim_time_period tp ON obs.period_key = tp.period_key
            WHERE o.soc_code = ? AND o.is_current = true
              AND m.metric_name = ? AND g.geo_type = ?
              AND obs.comparability_mode = ?
            ORDER BY tp.year
        """,
            [code, metric, geo_type, comparability_mode],
        ).fetchall()

        title = rows[0][2] if rows else code
        results.append(
            {
                "soc_code": code,
                "title": title,
                "series": [{"year": r[0], "value": r[1]} for r in rows],
            }
        )

    return {"metric": metric, "geo_type": geo_type, "occupations": results}


@router.get("/trends/compare/geography")
def compare_geography(
    soc_code: str = Query(..., description="SOC code"),
    metric: str = Query("mean_annual_wage"),
    year: int | None = Query(None, description="Specific year (latest if omitted)"),
) -> dict:
    """Compare a metric for one occupation across states."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code: {soc_code}")

    conn = get_db()

    if not _table_exists(conn, "fact_time_series_observation"):
        return {"soc_code": soc_code, "metric": metric, "geographies": []}

    if year is None:
        yr = conn.execute(
            """
            SELECT MAX(tp.year)
            FROM fact_time_series_observation obs
            JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
            JOIN dim_metric m ON obs.metric_key = m.metric_key
            JOIN dim_geography g ON obs.geography_key = g.geography_key
            JOIN dim_time_period tp ON obs.period_key = tp.period_key
            WHERE o.soc_code = ? AND m.metric_name = ? AND g.geo_type = 'state'
              AND obs.comparability_mode = 'as_published'
        """,
            [soc_code, metric],
        ).fetchone()
        year = yr[0] if yr and yr[0] else None

    if year is None:
        return {"soc_code": soc_code, "metric": metric, "year": None, "geographies": []}

    rows = conn.execute(
        """
        SELECT g.geo_name, g.geo_code, obs.observed_value, obs.source_release_id
        FROM fact_time_series_observation obs
        JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
        JOIN dim_metric m ON obs.metric_key = m.metric_key
        JOIN dim_geography g ON obs.geography_key = g.geography_key
        JOIN dim_time_period tp ON obs.period_key = tp.period_key
        WHERE o.soc_code = ? AND o.is_current = true
          AND m.metric_name = ?
          AND g.geo_type = 'state'
          AND tp.year = ?
          AND obs.comparability_mode = 'as_published'
        ORDER BY g.geo_name
    """,
        [soc_code, metric, year],
    ).fetchall()

    return {
        "soc_code": soc_code,
        "metric": metric,
        "year": year,
        "geographies": [{"geo_name": r[0], "geo_code": r[1], "value": r[2], "source_release_id": r[3]} for r in rows],
    }


@router.get("/trends/movers")
def ranked_movers(
    metric: str = Query("employment_count"),
    geo_type: str = Query("national"),
    year: int | None = Query(None, description="Specific year (latest if omitted)"),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Return top gainers and losers by metric change."""
    conn = get_db()

    if not _table_exists(conn, "fact_derived_series"):
        return {"metric": metric, "year": None, "available_years": [], "gainers": [], "losers": []}

    # Get available years
    year_rows = conn.execute(
        """
        SELECT DISTINCT tp.year
        FROM fact_derived_series d
        JOIN dim_time_period tp ON d.period_key = tp.period_key
        JOIN dim_metric m ON d.metric_key = m.metric_key
        WHERE m.metric_name = 'yoy_percent_change'
        ORDER BY tp.year
    """
    ).fetchall()
    available_years = [r[0] for r in year_rows]

    if year is None and available_years:
        year = max(available_years)

    movers_sql = """
        SELECT
            o.soc_code, o.occupation_title,
            d.derived_value AS pct_change,
            abs.derived_value AS abs_change
        FROM fact_derived_series d
        JOIN dim_metric m ON d.metric_key = m.metric_key
        JOIN dim_metric bm ON d.base_metric_key = bm.metric_key
        JOIN dim_occupation o ON d.occupation_key = o.occupation_key
        JOIN dim_geography g ON d.geography_key = g.geography_key
        JOIN dim_time_period tp ON d.period_key = tp.period_key
        LEFT JOIN fact_derived_series abs
          ON abs.base_metric_key = d.base_metric_key
          AND abs.occupation_key = d.occupation_key
          AND abs.geography_key = d.geography_key
          AND abs.period_key = d.period_key
          AND abs.comparability_mode = d.comparability_mode
          AND abs.derivation_method = 'yoy_absolute_change'
        WHERE m.metric_name = 'yoy_percent_change'
          AND bm.metric_name = ?
          AND g.geo_type = ?
          AND tp.year = ?
          AND d.derived_value IS NOT NULL
          AND o.is_current = true
        ORDER BY d.derived_value {direction}
        LIMIT ?
    """

    gainers = conn.execute(
        movers_sql.format(direction="DESC"),
        [metric, geo_type, year, limit],
    ).fetchall()

    losers = conn.execute(
        movers_sql.format(direction="ASC"),
        [metric, geo_type, year, limit],
    ).fetchall()

    def _mover_row(r):
        return {"soc_code": r[0], "title": r[1], "pct_change": r[2], "abs_change": r[3]}

    return {
        "metric": metric,
        "geo_type": geo_type,
        "year": year,
        "available_years": available_years,
        "gainers": [_mover_row(r) for r in gainers],
        "losers": [_mover_row(r) for r in losers],
    }


@router.get("/trends/metrics")
def list_metrics() -> dict:
    """Return available metrics for trend analysis."""
    conn = get_db()

    if not _table_exists(conn, "dim_metric"):
        return {"metrics": []}

    rows = conn.execute("""
        SELECT metric_name, units, display_format, derivation_type,
               comparability_constraint, description
        FROM dim_metric
        ORDER BY derivation_type, metric_name
    """).fetchall()

    return {
        "metrics": [
            {
                "metric_name": r[0],
                "units": r[1],
                "display_format": r[2],
                "derivation_type": r[3],
                "comparability_constraint": r[4],
                "description": r[5],
            }
            for r in rows
        ],
    }


@router.get("/trends/{soc_code}")
def occupation_trend(
    soc_code: str,
    metric: str = Query("employment_count", description="Metric name"),
    geo_type: str = Query("national", description="Geography type"),
    comparability_mode: str = Query("as_published", description="as_published or comparable"),
) -> dict:
    """Return time-series trend data for one occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code: {soc_code}")

    conn = get_db()

    if not _table_exists(conn, "fact_time_series_observation"):
        return {"soc_code": soc_code, "metric": metric, "series": []}

    rows = conn.execute(
        """
        SELECT
            tp.year,
            obs.observed_value,
            obs.suppression_flag,
            obs.source_release_id,
            m.metric_name,
            m.units,
            m.derivation_type,
            g.geo_name,
            d_yoy.derived_value AS yoy_change,
            d_pct.derived_value AS yoy_pct_change
        FROM fact_time_series_observation obs
        JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
        JOIN dim_metric m ON obs.metric_key = m.metric_key
        JOIN dim_geography g ON obs.geography_key = g.geography_key
        JOIN dim_time_period tp ON obs.period_key = tp.period_key
        LEFT JOIN fact_derived_series d_yoy
          ON d_yoy.base_metric_key = obs.metric_key
          AND d_yoy.occupation_key = obs.occupation_key
          AND d_yoy.geography_key = obs.geography_key
          AND d_yoy.period_key = obs.period_key
          AND d_yoy.comparability_mode = obs.comparability_mode
          AND d_yoy.derivation_method = 'yoy_absolute_change'
        LEFT JOIN fact_derived_series d_pct
          ON d_pct.base_metric_key = obs.metric_key
          AND d_pct.occupation_key = obs.occupation_key
          AND d_pct.geography_key = obs.geography_key
          AND d_pct.period_key = obs.period_key
          AND d_pct.comparability_mode = obs.comparability_mode
          AND d_pct.derivation_method = 'yoy_percent_change'
        WHERE o.soc_code = ? AND o.is_current = true
          AND m.metric_name = ?
          AND g.geo_type = ?
          AND obs.comparability_mode = ?
        ORDER BY tp.year
    """,
        [soc_code, metric, geo_type, comparability_mode],
    ).fetchall()

    series = []
    for r in rows:
        series.append(
            {
                "year": r[0],
                "value": r[1],
                "suppressed": r[2],
                "source_release_id": r[3],
                "metric_name": r[4],
                "units": r[5],
                "derivation_type": r[6],
                "geo_name": r[7],
                "yoy_change": r[8],
                "yoy_pct_change": r[9],
            }
        )

    return {"soc_code": soc_code, "metric": metric, "geo_type": geo_type, "series": series}
