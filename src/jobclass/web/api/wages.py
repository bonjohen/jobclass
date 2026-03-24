"""Employment and wages API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query

from jobclass.web.api.models import GeographiesResponse, WagesResponse
from jobclass.web.database import get_db

router = APIRouter(prefix="/api", tags=["wages"])

_SOC_CODE_RE = re.compile(r"^\d{2}-\d{4}$")
_VALID_GEO_TYPES = {"national", "state"}


@router.get("/occupations/{soc_code}/wages", response_model=WagesResponse)
def occupation_wages(
    soc_code: str,
    geo_type: str = Query("national", description="Geography type: national or state"),
    limit: int = Query(100, ge=1, le=500, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> dict:
    """Return wage data for an occupation, optionally filtered by geography type."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    if geo_type not in _VALID_GEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid geo_type: {geo_type}. Must be one of: {', '.join(sorted(_VALID_GEO_TYPES))}",
        )
    conn = get_db()

    # Verify occupation exists
    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    # Use only the latest OEWS release to avoid duplicate rows per geography.
    latest_row = conn.execute(
        "SELECT MAX(source_release_id) FROM fact_occupation_employment_wages"
    ).fetchone()
    latest_release = latest_row[0] if latest_row else None

    count_row = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_occupation_employment_wages f
        JOIN dim_occupation o ON f.occupation_key = o.occupation_key
        JOIN dim_geography g ON f.geography_key = g.geography_key
        WHERE o.soc_code = ? AND o.is_current = true
          AND g.geo_type = ?
          AND f.source_release_id = ?
    """,
        [soc_code, geo_type, latest_release],
    ).fetchone()
    total = count_row[0] if count_row else 0

    rows = conn.execute(
        """
        SELECT
            g.geo_type, g.geo_code, g.geo_name,
            f.employment_count, f.mean_annual_wage, f.median_annual_wage,
            f.mean_hourly_wage, f.median_hourly_wage,
            f.p10_hourly_wage, f.p25_hourly_wage, f.p75_hourly_wage, f.p90_hourly_wage,
            f.source_release_id, f.reference_period
        FROM fact_occupation_employment_wages f
        JOIN dim_occupation o ON f.occupation_key = o.occupation_key
        JOIN dim_geography g ON f.geography_key = g.geography_key
        WHERE o.soc_code = ? AND o.is_current = true
          AND g.geo_type = ?
          AND f.source_release_id = ?
        ORDER BY g.geo_name
        LIMIT ? OFFSET ?
    """,
        [soc_code, geo_type, latest_release, limit, offset],
    ).fetchall()

    results = []
    for r in rows:
        results.append(
            {
                "geo_type": r[0],
                "geo_code": r[1],
                "geo_name": r[2],
                "employment_count": r[3],
                "mean_annual_wage": r[4],
                "median_annual_wage": r[5],
                "mean_hourly_wage": r[6],
                "median_hourly_wage": r[7],
                "p10_hourly_wage": r[8],
                "p25_hourly_wage": r[9],
                "p75_hourly_wage": r[10],
                "p90_hourly_wage": r[11],
                "source_release_id": r[12],
                "reference_period": r[13],
            }
        )

    return {
        "soc_code": soc_code,
        "geo_type": geo_type,
        "total": total,
        "limit": limit,
        "offset": offset,
        "wages": results,
    }


@router.get("/geographies", response_model=GeographiesResponse)
def list_geographies() -> dict:
    """Return all available geographies with metadata."""
    conn = get_db()
    rows = conn.execute("""
        SELECT geo_type, geo_code, geo_name
        FROM dim_geography
        WHERE is_current = true
        ORDER BY geo_type, geo_name
    """).fetchall()

    return {"geographies": [{"geo_type": r[0], "geo_code": r[1], "geo_name": r[2]} for r in rows]}
