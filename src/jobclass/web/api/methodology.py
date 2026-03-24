"""Methodology and data transparency API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter

from jobclass.web.api.models import SourcesResponse, ValidationResponse
from jobclass.web.database import get_db

_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")

router = APIRouter(prefix="/api/methodology", tags=["methodology"])


@router.get("/sources", response_model=SourcesResponse)
def data_sources() -> dict:
    """Return descriptions of all data sources with versions and refresh info."""
    conn = get_db()

    # Get current versions from warehouse
    soc_version = None
    try:
        row = conn.execute(
            "SELECT DISTINCT soc_version FROM dim_occupation WHERE is_current = true LIMIT 1"
        ).fetchone()
        if row:
            soc_version = row[0]
    except Exception:
        pass

    oews_release = None
    try:
        row = conn.execute(
            "SELECT DISTINCT source_release_id FROM fact_occupation_employment_wages LIMIT 1"
        ).fetchone()
        if row:
            oews_release = row[0]
    except Exception:
        pass

    onet_version = None
    try:
        row = conn.execute(
            "SELECT DISTINCT source_version FROM dim_skill WHERE is_current = true LIMIT 1"
        ).fetchone()
        if row:
            onet_version = row[0]
    except Exception:
        pass

    proj_cycle = None
    try:
        row = conn.execute(
            "SELECT DISTINCT projection_cycle FROM fact_occupation_projections LIMIT 1"
        ).fetchone()
        if row:
            proj_cycle = row[0]
    except Exception:
        pass

    sources = [
        {
            "name": "Standard Occupational Classification (SOC)",
            "provider": "Bureau of Labor Statistics",
            "role": "Occupation taxonomy backbone — hierarchy from major groups to detailed occupations",
            "url": "https://www.bls.gov/soc/",
            "current_version": soc_version,
            "refresh_cadence": "Revised approximately every 10 years",
        },
        {
            "name": "Occupational Employment and Wage Statistics (OEWS)",
            "provider": "Bureau of Labor Statistics",
            "role": "Employment counts and wage measures by occupation, geography, and industry",
            "url": "https://www.bls.gov/oes/",
            "current_version": oews_release,
            "refresh_cadence": "Annual",
        },
        {
            "name": "O*NET (Occupational Information Network)",
            "provider": "Department of Labor / O*NET Center",
            "role": "Semantic descriptors — skills, knowledge, abilities, and tasks for each occupation",
            "url": "https://www.onetcenter.org/",
            "current_version": onet_version,
            "refresh_cadence": "Semi-annual",
        },
        {
            "name": "Employment Projections",
            "provider": "Bureau of Labor Statistics",
            "role": "10-year employment outlook with growth rates and education requirements",
            "url": "https://www.bls.gov/emp/",
            "current_version": proj_cycle,
            "refresh_cadence": "Biennial",
        },
    ]

    return {"sources": sources}


@router.get("/validation", response_model=ValidationResponse)
def validation_summary() -> dict:
    """Return summary of pipeline validation status."""
    conn = get_db()

    checks: list[dict] = []

    # Check dim_occupation has rows
    row = conn.execute("SELECT COUNT(*) FROM dim_occupation WHERE is_current = true").fetchone()
    occ_count = row[0] if row else 0
    checks.append({
        "check": "dim_occupation populated",
        "passed": occ_count > 0,
        "detail": f"{occ_count} current occupations loaded",
    })

    # Check fact table has rows
    row = conn.execute("SELECT COUNT(*) FROM fact_occupation_employment_wages").fetchone()
    fact_count = row[0] if row else 0
    checks.append({
        "check": "fact_occupation_employment_wages populated",
        "passed": fact_count > 0,
        "detail": f"{fact_count} wage fact rows loaded",
    })

    # Check skills bridge
    row = conn.execute("SELECT COUNT(*) FROM bridge_occupation_skill").fetchone()
    skill_count = row[0] if row else 0
    checks.append({
        "check": "bridge_occupation_skill populated",
        "passed": skill_count > 0,
        "detail": f"{skill_count} skill-occupation links loaded",
    })

    # Check tasks bridge
    row = conn.execute("SELECT COUNT(*) FROM bridge_occupation_task").fetchone()
    task_count = row[0] if row else 0
    checks.append({
        "check": "bridge_occupation_task populated",
        "passed": task_count > 0,
        "detail": f"{task_count} task-occupation links loaded",
    })

    # Check projections
    try:
        row = conn.execute("SELECT COUNT(*) FROM fact_occupation_projections").fetchone()
        proj_count = row[0] if row else 0
    except Exception:
        proj_count = 0
    checks.append({
        "check": "fact_occupation_projections populated",
        "passed": proj_count > 0,
        "detail": f"{proj_count} projection fact rows loaded",
    })

    # Check all marts exist
    mart_views = [
        "occupation_summary", "occupation_wages_by_geography",
        "occupation_skill_profile", "occupation_task_profile",
        "occupation_similarity_seeded",
    ]
    for view in mart_views:
        try:
            if not _IDENTIFIER_RE.match(view):
                raise ValueError(f"Invalid view name: {view!r}")
            row = conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()
            count = row[0] if row else 0
            checks.append({
                "check": f"mart view '{view}' queryable",
                "passed": count > 0,
                "detail": f"{count} rows",
            })
        except Exception:
            checks.append({
                "check": f"mart view '{view}' queryable",
                "passed": False,
                "detail": "View not found or query failed",
            })

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)

    return {
        "total_checks": total,
        "passed": passed,
        "failed": total - passed,
        "all_passed": passed == total,
        "checks": checks,
    }
