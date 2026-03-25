"""Skills, tasks, and similarity API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from jobclass.web.api.models import (
    AbilitiesResponse,
    ActivitiesResponse,
    EducationResponse,
    KnowledgeResponse,
    SimilarResponse,
    SkillsResponse,
    TasksResponse,
    TechnologyResponse,
)
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
    rows = conn.execute(
        """
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
    """,
        [occ[0]],
    ).fetchall()

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


@router.get("/occupations/{soc_code}/knowledge", response_model=KnowledgeResponse)
def occupation_knowledge(soc_code: str) -> dict:
    """Return knowledge domain scores for an occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    rows = conn.execute(
        """
        SELECT
            k.element_name,
            k.element_id,
            MAX(CASE WHEN b.scale_id = 'IM' THEN b.data_value END) AS importance,
            MAX(CASE WHEN b.scale_id = 'LV' THEN b.data_value END) AS level
        FROM bridge_occupation_knowledge b
        JOIN dim_knowledge k ON b.knowledge_key = k.knowledge_key
        WHERE b.occupation_key = ? AND k.is_current = true
        GROUP BY k.element_name, k.element_id
        ORDER BY importance DESC NULLS LAST
    """,
        [occ[0]],
    ).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_knowledge WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "knowledge": [
            {
                "element_name": r[0],
                "element_id": r[1],
                "importance": r[2],
                "level": r[3],
            }
            for r in rows
        ],
    }


@router.get("/occupations/{soc_code}/abilities", response_model=AbilitiesResponse)
def occupation_abilities(soc_code: str) -> dict:
    """Return ability scores for an occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    rows = conn.execute(
        """
        SELECT
            a.element_name,
            a.element_id,
            MAX(CASE WHEN b.scale_id = 'IM' THEN b.data_value END) AS importance,
            MAX(CASE WHEN b.scale_id = 'LV' THEN b.data_value END) AS level
        FROM bridge_occupation_ability b
        JOIN dim_ability a ON b.ability_key = a.ability_key
        WHERE b.occupation_key = ? AND a.is_current = true
        GROUP BY a.element_name, a.element_id
        ORDER BY importance DESC NULLS LAST
    """,
        [occ[0]],
    ).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_ability WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "abilities": [
            {
                "element_name": r[0],
                "element_id": r[1],
                "importance": r[2],
                "level": r[3],
            }
            for r in rows
        ],
    }


@router.get("/occupations/{soc_code}/activities", response_model=ActivitiesResponse)
def occupation_activities(soc_code: str) -> dict:
    """Return work activity scores for an occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    rows = conn.execute(
        """
        SELECT
            w.element_name,
            w.element_id,
            MAX(CASE WHEN b.scale_id = 'IM' THEN b.data_value END) AS importance,
            MAX(CASE WHEN b.scale_id = 'LV' THEN b.data_value END) AS level
        FROM bridge_occupation_work_activity b
        JOIN dim_work_activity w ON b.work_activity_key = w.work_activity_key
        WHERE b.occupation_key = ? AND w.is_current = true
        GROUP BY w.element_name, w.element_id
        ORDER BY importance DESC NULLS LAST
    """,
        [occ[0]],
    ).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_work_activity WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "activities": [
            {
                "element_name": r[0],
                "element_id": r[1],
                "importance": r[2],
                "level": r[3],
            }
            for r in rows
        ],
    }


@router.get("/occupations/{soc_code}/education", response_model=EducationResponse)
def occupation_education(soc_code: str) -> dict:
    """Return education and training requirements for an occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    rows = conn.execute(
        """
        SELECT
            d.element_id,
            d.element_name,
            d.scale_id,
            d.category,
            d.category_label,
            b.data_value
        FROM bridge_occupation_education b
        JOIN dim_education_requirement d ON b.education_key = d.education_key
        WHERE b.occupation_key = ? AND d.is_current = true
        ORDER BY d.element_id, d.category
    """,
        [occ[0]],
    ).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_education WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    # Group by element
    elements: dict[str, dict] = {}
    for r in rows:
        eid = r[0]
        if eid not in elements:
            elements[eid] = {
                "element_id": eid,
                "element_name": r[1],
                "scale_id": r[2],
                "categories": [],
            }
        elements[eid]["categories"].append(
            {
                "category": r[3],
                "category_label": r[4],
                "percentage": r[5],
            }
        )

    # Build summary from Required Level of Education (highest percentage category)
    summary = None
    education_labels = {
        1: "Less than high school",
        2: "High school diploma or equivalent",
        3: "Some college, no degree",
        4: "Postsecondary non-degree award",
        5: "Associate's degree",
        6: "Bachelor's degree",
        7: "Master's degree",
        8: "Doctoral or professional degree",
    }
    for elem in elements.values():
        if elem["scale_id"] == "RL":
            best = max(elem["categories"], key=lambda c: c["percentage"] or 0, default=None)
            if best and best["percentage"]:
                label = education_labels.get(best["category"], f"Category {best['category']}")
                summary = f"Typical: {label} ({best['percentage']:.0f}%)"
            break

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "summary": summary,
        "elements": list(elements.values()),
    }


@router.get("/occupations/{soc_code}/technology", response_model=TechnologyResponse)
def occupation_technology(soc_code: str) -> dict:
    """Return tools and technology used by an occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    occ = conn.execute(
        "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND is_current = true",
        [soc_code],
    ).fetchone()
    if not occ:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    rows = conn.execute(
        """
        SELECT
            t.t2_type,
            t.example_name,
            t.commodity_code,
            t.commodity_title,
            b.hot_technology
        FROM bridge_occupation_technology b
        JOIN dim_technology t ON b.technology_key = t.technology_key
        WHERE b.occupation_key = ? AND t.is_current = true
        ORDER BY t.t2_type, t.example_name
    """,
        [occ[0]],
    ).fetchall()

    source_version = None
    ver_row = conn.execute(
        "SELECT DISTINCT source_version FROM bridge_occupation_technology WHERE occupation_key = ? LIMIT 1",
        [occ[0]],
    ).fetchone()
    if ver_row:
        source_version = ver_row[0]

    # Group by t2_type
    groups: dict[str, list] = {}
    for r in rows:
        t2_type = r[0]
        if t2_type not in groups:
            groups[t2_type] = []
        groups[t2_type].append(
            {
                "example_name": r[1],
                "commodity_code": r[2],
                "commodity_title": r[3],
                "hot_technology": r[4],
            }
        )

    return {
        "soc_code": soc_code,
        "source_version": source_version,
        "groups": [{"t2_type": k, "items": v} for k, v in groups.items()],
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

    rows = conn.execute(
        """
        SELECT t.task, b.data_value, t.task_id
        FROM bridge_occupation_task b
        JOIN dim_task t ON b.task_key = t.task_key
        WHERE b.occupation_key = ? AND t.is_current = true
        ORDER BY b.data_value DESC NULLS LAST
    """,
        [occ[0]],
    ).fetchall()

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

    rows = conn.execute(
        """
        SELECT
            CASE WHEN occupation_key_a = ? THEN soc_code_b ELSE soc_code_a END AS other_code,
            CASE WHEN occupation_key_a = ? THEN title_b ELSE title_a END AS other_title,
            jaccard_similarity
        FROM occupation_similarity_seeded
        WHERE occupation_key_a = ? OR occupation_key_b = ?
        ORDER BY jaccard_similarity DESC
        LIMIT 10
    """,
        [occ_key, occ_key, occ_key, occ_key],
    ).fetchall()

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
