"""Skills, tasks, and similarity API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from jobclass.web.api.models import SimilarResponse, SkillsResponse, TasksResponse
from jobclass.web.database import get_db

router = APIRouter(prefix="/api", tags=["skills"])

_SOC_CODE_RE = re.compile(r"^\d{2}-\d{4}$")


@router.get("/occupations/{soc_code}/skills", response_model=SkillsResponse)
def occupation_skills(soc_code: str) -> dict:
    """Return skill profile for an occupation with importance and level scores."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    # Pivot importance (IM) and level (LV) into single rows per skill
    rows = conn.execute("""
        SELECT
            s.element_name,
            s.element_id,
            MAX(CASE WHEN b.scale_id = 'IM' THEN b.data_value END) AS importance,
            MAX(CASE WHEN b.scale_id = 'LV' THEN b.data_value END) AS level
        FROM bridge_occupation_skill b
        JOIN dim_skill s ON b.skill_key = s.skill_key
        WHERE b.occupation_key = ? AND s.is_current = true
        GROUP BY s.element_name, s.element_id
        ORDER BY importance DESC NULLS LAST
    """, [occ[0]]).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_skill WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "skills": [
            {
                "element_name": r[0],
                "element_id": r[1],
                "importance": r[2],
                "level": r[3],
            }
            for r in rows
        ],
    }


@router.get("/occupations/{soc_code}/tasks", response_model=TasksResponse)
def occupation_tasks(soc_code: str) -> dict:
    """Return task profile for an occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    rows = conn.execute("""
        SELECT t.task, b.data_value, t.task_id
        FROM bridge_occupation_task b
        JOIN dim_task t ON b.task_key = t.task_key
        WHERE b.occupation_key = ? AND t.is_current = true
        ORDER BY b.data_value DESC NULLS LAST
    """, [occ[0]]).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_task WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "tasks": [
            {
                "task_description": r[0],
                "relevance_score": r[1],
                "task_id": r[2],
            }
            for r in rows
        ],
    }


@router.get("/occupations/{soc_code}/similar", response_model=SimilarResponse)
def similar_occupations(soc_code: str) -> dict:
    """Return similar occupations based on Jaccard skill similarity."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    occ_key = occ[0]

    rows = conn.execute("""
        SELECT
            CASE WHEN occupation_key_a = ? THEN soc_code_b ELSE soc_code_a END AS other_code,
            CASE WHEN occupation_key_a = ? THEN title_b ELSE title_a END AS other_title,
            jaccard_similarity
        FROM occupation_similarity_seeded
        WHERE occupation_key_a = ? OR occupation_key_b = ?
        ORDER BY jaccard_similarity DESC
        LIMIT 10
    """, [occ_key, occ_key, occ_key, occ_key]).fetchall()

    return {
        "soc_code": soc_code,
        "similar": [
            {
                "soc_code": r[0],
                "occupation_title": r[1],
                "similarity_score": r[2],
            }
            for r in rows
        ],
    }
