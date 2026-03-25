"""CPI domain API endpoints — search, member detail, hierarchy, series, areas."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from jobclass.web.api.models import (
    CpiAreaDetail,
    CpiAreaMembersResponse,
    CpiAveragePriceResponse,
    CpiChildrenResponse,
    CpiExplorerNode,
    CpiImportanceResponse,
    CpiMemberDetail,
    CpiRelationsResponse,
    CpiRevisionVintageResponse,
    CpiSearchResponse,
    CpiSeriesResponse,
)
from jobclass.web.database import get_db

router = APIRouter(prefix="/api/cpi", tags=["cpi"])


def _table_exists(conn, table_name: str) -> bool:
    """Check if a CPI table exists in the database."""
    try:
        conn.execute(f"SELECT 1 FROM {table_name} LIMIT 0")  # noqa: S608
        return True
    except Exception:
        return False


@router.get("/search", response_model=CpiSearchResponse)
def cpi_search(
    q: str = Query("", max_length=200, description="Search CPI members by name or code"),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Search CPI members by name or item code."""
    conn = get_db()
    q = q.strip()
    if not q or not _table_exists(conn, "dim_cpi_member"):
        return {"query": q, "total": 0, "results": []}

    rows = conn.execute(
        """SELECT member_code, title, hierarchy_level, semantic_role
           FROM dim_cpi_member
           WHERE member_code ILIKE ? OR title ILIKE ?
           ORDER BY member_code
           LIMIT ?""",
        [f"%{q}%", f"%{q}%", limit],
    ).fetchall()

    total = conn.execute(
        """SELECT COUNT(*) FROM dim_cpi_member
           WHERE member_code ILIKE ? OR title ILIKE ?""",
        [f"%{q}%", f"%{q}%"],
    ).fetchone()[0]

    return {
        "query": q,
        "total": total,
        "results": [
            {
                "member_code": r[0],
                "title": r[1],
                "hierarchy_level": r[2],
                "semantic_role": r[3],
            }
            for r in rows
        ],
    }


@router.get("/members/{member_code}", response_model=CpiMemberDetail)
def cpi_member_detail(member_code: str) -> dict:
    """Get CPI member detail with hierarchy position and metadata."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    row = conn.execute(
        """SELECT member_key, member_code, title, hierarchy_level, semantic_role,
                  is_cross_cutting, has_average_price, has_relative_importance
           FROM dim_cpi_member
           WHERE member_code = ?
           LIMIT 1""",
        [member_code.upper()],
    ).fetchone()
    if not row:
        raise HTTPException(404, f"CPI member {member_code} not found")

    member_key = row[0]

    # Count variants
    variant_count = 0
    if _table_exists(conn, "dim_cpi_series_variant"):
        variant_count = conn.execute(
            "SELECT COUNT(*) FROM dim_cpi_series_variant WHERE member_key = ?",
            [member_key],
        ).fetchone()[0]

    # Count children
    children_count = 0
    if _table_exists(conn, "bridge_cpi_member_hierarchy"):
        children_count = conn.execute(
            "SELECT COUNT(*) FROM bridge_cpi_member_hierarchy WHERE parent_member_key = ?",
            [member_key],
        ).fetchone()[0]

    # Build ancestor chain
    ancestors = []
    if _table_exists(conn, "bridge_cpi_member_hierarchy"):
        current_key = member_key
        visited = set()
        while current_key and current_key not in visited:
            visited.add(current_key)
            parent_row = conn.execute(
                """SELECT p.member_code, p.title, p.hierarchy_level, p.semantic_role,
                          p.member_key
                   FROM bridge_cpi_member_hierarchy b
                   JOIN dim_cpi_member p ON p.member_key = b.parent_member_key
                   WHERE b.child_member_key = ?""",
                [current_key],
            ).fetchone()
            if parent_row:
                ancestors.insert(0, {
                    "member_code": parent_row[0],
                    "title": parent_row[1],
                    "hierarchy_level": parent_row[2],
                    "semantic_role": parent_row[3],
                })
                current_key = parent_row[4]
            else:
                break

    return {
        "member_code": row[1],
        "title": row[2],
        "hierarchy_level": row[3],
        "semantic_role": row[4],
        "is_cross_cutting": row[5],
        "has_average_price": row[6],
        "has_relative_importance": row[7],
        "variant_count": variant_count,
        "children_count": children_count,
        "ancestors": ancestors,
    }


@router.get("/members/{member_code}/children", response_model=CpiChildrenResponse)
def cpi_member_children(member_code: str) -> dict:
    """List direct child members in hierarchy order."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    parent = conn.execute(
        "SELECT member_key FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not parent:
        raise HTTPException(404, f"CPI member {member_code} not found")

    children = []
    if _table_exists(conn, "bridge_cpi_member_hierarchy"):
        rows = conn.execute(
            """SELECT c.member_code, c.title, c.hierarchy_level, c.semantic_role
               FROM bridge_cpi_member_hierarchy b
               JOIN dim_cpi_member c ON c.member_key = b.child_member_key
               WHERE b.parent_member_key = ?
               ORDER BY c.member_code""",
            [parent[0]],
        ).fetchall()
        children = [
            {
                "member_code": r[0],
                "title": r[1],
                "hierarchy_level": r[2],
                "semantic_role": r[3],
            }
            for r in rows
        ]

    return {"member_code": member_code.upper(), "children": children}


@router.get("/members/{member_code}/relations", response_model=CpiRelationsResponse)
def cpi_member_relations(member_code: str) -> dict:
    """List cross-cutting relationships for a member."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    relations = []
    if _table_exists(conn, "bridge_cpi_member_relation"):
        rows = conn.execute(
            """SELECT m.member_code, m.title, b.relation_type, b.description
               FROM bridge_cpi_member_relation b
               JOIN dim_cpi_member m ON m.member_key = b.member_key_b
               WHERE b.member_key_a = ?
               UNION ALL
               SELECT m.member_code, m.title, b.relation_type, b.description
               FROM bridge_cpi_member_relation b
               JOIN dim_cpi_member m ON m.member_key = b.member_key_a
               WHERE b.member_key_b = ?
               ORDER BY 3, 1""",
            [member[0], member[0]],
        ).fetchall()
        relations = [
            {
                "member_code": r[0],
                "title": r[1],
                "relation_type": r[2],
                "description": r[3],
            }
            for r in rows
        ]

    return {"member_code": member_code.upper(), "relations": relations}


@router.get("/members/{member_code}/series", response_model=CpiSeriesResponse)
def cpi_member_series(
    member_code: str,
    area_code: str = Query("0000", description="Area code filter"),
    index_family: str = Query("CPI-U", description="Index family"),
    seasonal_adjustment: str = Query("S", description="S=seasonally adjusted, U=not"),
) -> dict:
    """Time-series index values for a CPI member."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key, title FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    series = []
    if _table_exists(conn, "fact_cpi_observation") and _table_exists(conn, "dim_cpi_series_variant"):
        rows = conn.execute(
            """SELECT tp.year, 'M13' AS period, f.index_value
               FROM fact_cpi_observation f
               JOIN dim_cpi_series_variant v ON v.variant_key = f.variant_key
               JOIN dim_time_period tp ON tp.period_key = f.time_period_key
               WHERE v.member_key = ?
                 AND v.area_code = ?
                 AND v.index_family = ?
                 AND v.seasonal_adjustment = ?
               ORDER BY tp.year""",
            [member[0], area_code, index_family, seasonal_adjustment],
        ).fetchall()
        series = [{"year": r[0], "period": r[1], "value": r[2]} for r in rows]

    return {
        "member_code": member_code.upper(),
        "title": member[1],
        "area_code": area_code,
        "index_family": index_family,
        "seasonal_adjustment": seasonal_adjustment,
        "series": series,
    }


@router.get("/members/{member_code}/siblings")
def cpi_member_siblings(member_code: str) -> dict:
    """List sibling members (same parent) for comparison."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    siblings = []
    if _table_exists(conn, "bridge_cpi_member_hierarchy"):
        # Find parent, then get all children of that parent
        parent = conn.execute(
            "SELECT parent_member_key FROM bridge_cpi_member_hierarchy WHERE child_member_key = ?",
            [member[0]],
        ).fetchone()
        if parent:
            rows = conn.execute(
                """SELECT c.member_code, c.title, c.hierarchy_level, c.semantic_role
                   FROM bridge_cpi_member_hierarchy b
                   JOIN dim_cpi_member c ON c.member_key = b.child_member_key
                   WHERE b.parent_member_key = ? AND b.child_member_key != ?
                   ORDER BY c.member_code""",
                [parent[0], member[0]],
            ).fetchall()
            siblings = [
                {"member_code": r[0], "title": r[1], "hierarchy_level": r[2], "semantic_role": r[3]}
                for r in rows
            ]

    return {"member_code": member_code.upper(), "siblings": siblings}


@router.get("/members/{member_code}/variants")
def cpi_member_variants(member_code: str) -> dict:
    """List available series variants for a member with area details."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    variants = []
    if _table_exists(conn, "dim_cpi_series_variant"):
        rows = conn.execute(
            """SELECT v.series_id, v.index_family, v.seasonal_adjustment, v.periodicity,
                      v.area_code, a.area_title, a.publication_frequency
               FROM dim_cpi_series_variant v
               LEFT JOIN dim_cpi_area a ON a.area_key = v.area_key
               WHERE v.member_key = ?
               ORDER BY v.index_family, v.seasonal_adjustment, v.area_code""",
            [member[0]],
        ).fetchall()
        variants = [
            {
                "series_id": r[0],
                "index_family": r[1],
                "seasonal_adjustment": r[2],
                "periodicity": r[3],
                "area_code": r[4],
                "area_title": r[5] or r[4],
                "publication_frequency": r[6] or "monthly",
            }
            for r in rows
        ]

    return {"member_code": member_code.upper(), "variants": variants}


@router.get("/areas/{area_code}", response_model=CpiAreaDetail)
def cpi_area_detail(area_code: str) -> dict:
    """Get CPI area detail with publication rules."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_area"):
        raise HTTPException(404, "CPI data not loaded")

    row = conn.execute(
        """SELECT area_key, area_code, area_title, area_type, publication_frequency
           FROM dim_cpi_area
           WHERE area_code = ?
           LIMIT 1""",
        [area_code],
    ).fetchone()
    if not row:
        raise HTTPException(404, f"CPI area {area_code} not found")

    # Count published members for this area
    member_count = 0
    if _table_exists(conn, "dim_cpi_series_variant"):
        member_count = conn.execute(
            "SELECT COUNT(DISTINCT member_key) FROM dim_cpi_series_variant WHERE area_key = ?",
            [row[0]],
        ).fetchone()[0]

    return {
        "area_code": row[1],
        "area_title": row[2],
        "area_type": row[3],
        "publication_frequency": row[4],
        "member_count": member_count,
    }


@router.get("/areas/{area_code}/members", response_model=CpiAreaMembersResponse)
def cpi_area_members(area_code: str) -> dict:
    """List CPI members published in a specific area."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_area"):
        raise HTTPException(404, "CPI data not loaded")

    area = conn.execute(
        "SELECT area_key FROM dim_cpi_area WHERE area_code = ?",
        [area_code],
    ).fetchone()
    if not area:
        raise HTTPException(404, f"CPI area {area_code} not found")

    members = []
    if _table_exists(conn, "dim_cpi_series_variant"):
        rows = conn.execute(
            """SELECT DISTINCT m.member_code, m.title, m.hierarchy_level, m.semantic_role
               FROM dim_cpi_series_variant v
               JOIN dim_cpi_member m ON m.member_key = v.member_key
               WHERE v.area_key = ?
               ORDER BY m.member_code""",
            [area[0]],
        ).fetchall()
        members = [
            {
                "member_code": r[0],
                "title": r[1],
                "hierarchy_level": r[2],
                "semantic_role": r[3],
            }
            for r in rows
        ]

    return {"area_code": area_code, "members": members}


@router.get("/members/{member_code}/importance", response_model=CpiImportanceResponse)
def cpi_member_importance(
    member_code: str,
    area_code: str = Query("0000", description="Area code filter"),
) -> dict:
    """Return relative importance history for a CPI member."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key, title FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    entries = []
    if _table_exists(conn, "fact_cpi_relative_importance"):
        if area_code == "all":
            rows = conn.execute(
                """SELECT f.reference_period, f.relative_importance_value,
                          a.area_code
                   FROM fact_cpi_relative_importance f
                   JOIN dim_cpi_area a ON a.area_key = f.area_key
                   WHERE f.member_key = ?
                   ORDER BY f.reference_period, a.area_code""",
                [member[0]],
            ).fetchall()
        else:
            area = conn.execute(
                "SELECT area_key FROM dim_cpi_area WHERE area_code = ?",
                [area_code],
            ).fetchone()
            if area:
                rows = conn.execute(
                    """SELECT reference_period, relative_importance_value, ?
                       FROM fact_cpi_relative_importance
                       WHERE member_key = ? AND area_key = ?
                       ORDER BY reference_period""",
                    [area_code, member[0], area[0]],
                ).fetchall()
            else:
                rows = []
        entries = [
            {
                "reference_period": r[0],
                "relative_importance": r[1],
                "area_code": r[2],
            }
            for r in rows
        ]

    return {
        "member_code": member_code.upper(),
        "title": member[1],
        "entries": entries,
    }


@router.get("/members/{member_code}/average-prices", response_model=CpiAveragePriceResponse)
def cpi_member_average_prices(
    member_code: str,
    area_code: str = Query("0000", description="Area code filter"),
) -> dict:
    """Return average price history for applicable CPI items (food, utility, motor fuel)."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key, title, has_average_price FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    entries = []
    if _table_exists(conn, "fact_cpi_average_price"):
        area = conn.execute(
            "SELECT area_key FROM dim_cpi_area WHERE area_code = ?",
            [area_code],
        ).fetchone()
        if area:
            rows = conn.execute(
                """SELECT tp.year, 'M13' AS period, f.average_price, f.unit_description
                   FROM fact_cpi_average_price f
                   JOIN dim_time_period tp ON tp.period_key = f.time_period_key
                   WHERE f.member_key = ? AND f.area_key = ?
                   ORDER BY tp.year""",
                [member[0], area[0]],
            ).fetchall()
            entries = [
                {"year": r[0], "period": r[1], "average_price": r[2], "unit_description": r[3]}
                for r in rows
            ]

    return {
        "member_code": member_code.upper(),
        "title": member[1],
        "entries": entries,
    }


@router.get("/members/{member_code}/revisions", response_model=CpiRevisionVintageResponse)
def cpi_member_revisions(
    member_code: str,
    area_code: str = Query("0000", description="Area code filter"),
) -> dict:
    """Return revision vintage history for C-CPI-U members.

    Shows how preliminary values evolved into final values over successive BLS releases.
    """
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    member = conn.execute(
        "SELECT member_key, title FROM dim_cpi_member WHERE member_code = ?",
        [member_code.upper()],
    ).fetchone()
    if not member:
        raise HTTPException(404, f"CPI member {member_code} not found")

    entries = []
    if _table_exists(conn, "fact_cpi_revision_vintage"):
        area = conn.execute(
            "SELECT area_key FROM dim_cpi_area WHERE area_code = ?",
            [area_code],
        ).fetchone()
        if area:
            rows = conn.execute(
                """SELECT tp.year, 'M13' AS period, f.vintage_label,
                          f.index_value, f.is_preliminary
                   FROM fact_cpi_revision_vintage f
                   JOIN dim_time_period tp ON tp.period_key = f.time_period_key
                   WHERE f.member_key = ? AND f.area_key = ?
                   ORDER BY tp.year, f.vintage_label""",
                [member[0], area[0]],
            ).fetchall()
            entries = [
                {
                    "year": r[0],
                    "period": r[1],
                    "vintage_label": r[2],
                    "index_value": r[3],
                    "is_preliminary": r[4],
                }
                for r in rows
            ]

    return {
        "member_code": member_code.upper(),
        "title": member[1],
        "entries": entries,
    }


@router.get("/explorer/tree", response_model=CpiExplorerNode)
def cpi_explorer_tree(
    root: str = Query("SA0", description="Root member code"),
    max_depth: int = Query(2, ge=1, le=6, description="Max hierarchy depth"),
) -> dict:
    """Return a hierarchy tree with relative importance weights for the explorer visualization."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        raise HTTPException(404, "CPI data not loaded")

    root_row = conn.execute(
        "SELECT member_key, member_code, title, hierarchy_level FROM dim_cpi_member WHERE member_code = ?",
        [root.upper()],
    ).fetchone()
    if not root_row:
        raise HTTPException(404, f"CPI member {root} not found")

    # Build full parent→children map
    children_map: dict[int, list[tuple[int, str, str, str]]] = {}
    if _table_exists(conn, "bridge_cpi_member_hierarchy"):
        all_edges = conn.execute(
            """SELECT b.parent_member_key, b.child_member_key,
                      m.member_code, m.title, m.hierarchy_level
               FROM bridge_cpi_member_hierarchy b
               JOIN dim_cpi_member m ON m.member_key = b.child_member_key
               ORDER BY m.member_code""",
        ).fetchall()
        for edge in all_edges:
            children_map.setdefault(edge[0], []).append(
                (edge[1], edge[2], edge[3], edge[4])
            )

    # Build member_key → latest relative importance (national, latest period)
    importance_map: dict[int, float] = {}
    if _table_exists(conn, "fact_cpi_relative_importance"):
        ri_rows = conn.execute(
            """SELECT f.member_key, f.relative_importance_value
               FROM fact_cpi_relative_importance f
               JOIN dim_cpi_area a ON a.area_key = f.area_key AND a.area_code = '0000'
               WHERE f.reference_period = (
                   SELECT MAX(reference_period) FROM fact_cpi_relative_importance
               )""",
        ).fetchall()
        for r in ri_rows:
            importance_map[r[0]] = r[1]

    def build_node(member_key: int, code: str, title: str, level: str, depth: int) -> dict:
        node: dict = {
            "member_code": code,
            "title": title,
            "hierarchy_level": level,
            "relative_importance": importance_map.get(member_key),
            "children": [],
        }
        if depth < max_depth:
            for child_key, child_code, child_title, child_level in children_map.get(member_key, []):
                node["children"].append(
                    build_node(child_key, child_code, child_title, child_level, depth + 1)
                )
        return node

    return build_node(root_row[0], root_row[1], root_row[2], root_row[3], 0)


@router.get("/compare")
def cpi_compare(
    codes: str = Query("", description="Comma-separated member codes"),
    area_code: str = Query("0000", description="Area code"),
    index_family: str = Query("CPI-U", description="Index family"),
    seasonal_adjustment: str = Query("S", description="Seasonal adjustment"),
) -> dict:
    """Compare time series across multiple CPI members or areas."""
    conn = get_db()
    if not _table_exists(conn, "dim_cpi_member"):
        return {"codes": [], "series": {}}

    code_list = [c.strip().upper() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {"codes": [], "series": {}}

    result: dict[str, list] = {}
    for code in code_list[:10]:  # Max 10 members
        member = conn.execute(
            "SELECT member_key, title FROM dim_cpi_member WHERE member_code = ?",
            [code],
        ).fetchone()
        if not member:
            continue

        series_data = []
        if _table_exists(conn, "fact_cpi_observation") and _table_exists(conn, "dim_cpi_series_variant"):
            rows = conn.execute(
                """SELECT tp.year, f.index_value
                   FROM fact_cpi_observation f
                   JOIN dim_cpi_series_variant v ON v.variant_key = f.variant_key
                   JOIN dim_time_period tp ON tp.period_key = f.time_period_key
                   WHERE v.member_key = ?
                     AND v.area_code = ?
                     AND v.index_family = ?
                     AND v.seasonal_adjustment = ?
                   ORDER BY tp.year""",
                [member[0], area_code, index_family, seasonal_adjustment],
            ).fetchall()
            series_data = [{"year": r[0], "value": r[1]} for r in rows]

        result[code] = series_data

    return {"codes": code_list, "series": result}
