"""Employment projections API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from jobclass.web.database import get_db

router = APIRouter(prefix="/api", tags=["projections"])


@router.get("/occupations/{soc_code}/projections")
def occupation_projections(soc_code: str) -> dict:
    """Return employment projections for an occupation."""
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    row = conn.execute("""
        SELECT
            projection_cycle, base_year, projection_year,
            employment_base, employment_projected,
            employment_change_abs, employment_change_pct,
            annual_openings, education_category,
            training_category, work_experience_category,
            source_release_id
        FROM fact_occupation_projections
        WHERE occupation_key = ?
        ORDER BY projection_cycle DESC
        LIMIT 1
    """, [occ[0]]).fetchone()

    if not row:
        return {"soc_code": soc_code, "projections": None}

    return {
        "soc_code": soc_code,
        "projections": {
            "projection_cycle": row[0],
            "base_year": row[1],
            "projection_year": row[2],
            "base_employment": row[3],
            "projected_employment": row[4],
            "employment_change": row[5],
            "percent_change": row[6],
            "annual_openings": row[7],
            "education_category": row[8],
            "training_category": row[9],
            "work_experience_category": row[10],
            "source_release_id": row[11],
        },
    }
