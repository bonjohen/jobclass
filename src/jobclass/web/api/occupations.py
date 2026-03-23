"""Occupation search, hierarchy, and profile API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query

from jobclass.web.api.models import HierarchyResponse, OccupationProfileResponse, SearchResponse
from jobclass.web.database import get_db

router = APIRouter(prefix="/api", tags=["occupations"])

_SOC_CODE_RE = re.compile(r"^\d{2}-\d{4}$")


@router.get("/occupations/search", response_model=SearchResponse)
def search_occupations(q: str = Query("", max_length=100, description="Search keyword or SOC code")) -> dict:
    """Search occupations by keyword or SOC code."""
    conn = get_db()
    q = q.strip()
    if not q:
        return {"query": q, "results": []}

    rows = conn.execute("""
        SELECT soc_code, occupation_title, occupation_level, occupation_level_name
        FROM dim_occupation
        WHERE is_current = true
          AND (
            soc_code ILIKE ?
            OR occupation_title ILIKE ?
          )
        ORDER BY soc_code
    """, [f"%{q}%", f"%{q}%"]).fetchall()

    return {
        "query": q,
        "results": [
            {
                "soc_code": r[0],
                "occupation_title": r[1],
                "occupation_level": r[2],
                "occupation_level_name": r[3],
            }
            for r in rows
        ],
    }


@router.get("/occupations/hierarchy", response_model=HierarchyResponse)
def occupation_hierarchy() -> dict:
    """Return the full SOC hierarchy tree."""
    conn = get_db()

    rows = conn.execute("""
        SELECT soc_code, occupation_title, occupation_level, occupation_level_name, parent_soc_code
        FROM dim_occupation
        WHERE is_current = true
        ORDER BY soc_code
    """).fetchall()

    # Build tree: index all nodes, then wire parent-child relationships
    nodes: dict[str, dict] = {}
    for r in rows:
        nodes[r[0]] = {
            "soc_code": r[0],
            "occupation_title": r[1],
            "occupation_level": r[2],
            "occupation_level_name": r[3],
            "children": [],
        }

    roots: list[dict] = []
    for r in rows:
        soc_code, parent = r[0], r[4]
        if parent and parent in nodes:
            nodes[parent]["children"].append(nodes[soc_code])
        else:
            roots.append(nodes[soc_code])

    return {"hierarchy": roots}


@router.get("/occupations/{soc_code}", response_model=OccupationProfileResponse)
def occupation_profile(soc_code: str) -> dict:
    """Return full profile data for a single occupation."""
    if not _SOC_CODE_RE.match(soc_code):
        raise HTTPException(status_code=400, detail=f"Invalid SOC code format: {soc_code}")
    conn = get_db()

    row = conn.execute("""
        SELECT soc_code, occupation_title, occupation_level, occupation_level_name,
               parent_soc_code, major_group_code, minor_group_code,
               broad_occupation_code, detailed_occupation_code,
               occupation_definition, soc_version, is_leaf, source_release_id
        FROM dim_occupation
        WHERE soc_code = ? AND is_current = true
    """, [soc_code]).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

    # Build hierarchy breadcrumb
    breadcrumb = _build_breadcrumb(conn, row[5], row[6], row[7], row[0])

    # Sibling occupations (same parent)
    siblings = []
    if row[4]:
        sib_rows = conn.execute("""
            SELECT soc_code, occupation_title
            FROM dim_occupation
            WHERE parent_soc_code = ? AND soc_code != ? AND is_current = true
            ORDER BY soc_code
        """, [row[4], soc_code]).fetchall()
        siblings = [{"soc_code": s[0], "occupation_title": s[1]} for s in sib_rows]

    # Child occupations
    child_rows = conn.execute("""
        SELECT soc_code, occupation_title
        FROM dim_occupation
        WHERE parent_soc_code = ? AND is_current = true
        ORDER BY soc_code
    """, [soc_code]).fetchall()
    children = [{"soc_code": c[0], "occupation_title": c[1]} for c in child_rows]

    return {
        "soc_code": row[0],
        "occupation_title": row[1],
        "occupation_level": row[2],
        "occupation_level_name": row[3],
        "parent_soc_code": row[4],
        "major_group_code": row[5],
        "minor_group_code": row[6],
        "broad_occupation_code": row[7],
        "detailed_occupation_code": row[8],
        "occupation_definition": row[9],
        "soc_version": row[10],
        "is_leaf": row[11],
        "source_release_id": row[12],
        "breadcrumb": breadcrumb,
        "siblings": siblings,
        "children": children,
    }


def _build_breadcrumb(conn, major_code, minor_code, broad_code, current_code):
    """Build hierarchy breadcrumb from major group to current occupation."""
    codes = [c for c in [major_code, minor_code, broad_code, current_code] if c]
    # Deduplicate while preserving order
    seen = set()
    unique_codes = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            unique_codes.append(c)

    if not unique_codes:
        return []

    placeholders = ", ".join(["?"] * len(unique_codes))
    rows = conn.execute(f"""
        SELECT soc_code, occupation_title
        FROM dim_occupation
        WHERE soc_code IN ({placeholders}) AND is_current = true
    """, unique_codes).fetchall()

    lookup = {r[0]: r[1] for r in rows}
    return [{"soc_code": c, "occupation_title": lookup.get(c, c)} for c in unique_codes]
