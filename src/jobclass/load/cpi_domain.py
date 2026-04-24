"""CPI domain expansion loaders.

Loads parsed CPI data into warehouse dimensions, bridges, and facts.
The existing cpi.py handles the single-series deflator. This module
handles the full CPI analytical domain.
"""

from __future__ import annotations

import duckdb

from jobclass.parse.cpi_domain import (
    CpiAreaRow,
    CpiAveragePriceRow,
    CpiItemRow,
    CpiObservationRow,
    CpiOverlaySeriesRow,
    CpiRelativeImportanceRow,
    CpiRevisionVintageRow,
    CpiSeriesRow,
    _classify_publication_frequency,
    _classify_semantic_role,
)

# ---------------------------------------------------------------------------
# Staging loaders (delete-before-insert idempotency)
# ---------------------------------------------------------------------------


def load_cpi_item_hierarchy_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiItemRow],
    source_release_id: str,
) -> int:
    """Load parsed CPI item hierarchy rows into staging."""
    conn.execute(
        "DELETE FROM stage__bls__cpi_item_hierarchy WHERE source_release_id = ?",
        [source_release_id],
    )
    if rows:
        conn.executemany(
            """INSERT INTO stage__bls__cpi_item_hierarchy
                (item_code, item_name, hierarchy_level, parent_item_code,
                 sort_sequence, selectable, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    r.item_code,
                    r.item_name,
                    r.hierarchy_level,
                    r.parent_item_code,
                    r.sort_sequence,
                    r.selectable,
                    source_release_id,
                    r.parser_version,
                )
                for r in rows
            ],
        )
    return len(rows)


def load_cpi_series_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiSeriesRow],
    source_release_id: str,
) -> int:
    """Load parsed CPI series metadata into staging."""
    conn.execute(
        "DELETE FROM stage__bls__cpi_series WHERE source_release_id = ?",
        [source_release_id],
    )
    if rows:
        conn.executemany(
            """INSERT INTO stage__bls__cpi_series
                (series_id, index_family, seasonal_adjustment, periodicity,
                 area_code, item_code, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    r.series_id,
                    "CPI-U",
                    r.seasonal_adjustment,
                    r.periodicity,
                    r.area_code,
                    r.item_code,
                    source_release_id,
                    r.parser_version,
                )
                for r in rows
            ],
        )
    return len(rows)


def load_cpi_area_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiAreaRow],
    source_release_id: str,
) -> int:
    """Load parsed CPI area rows — no dedicated staging table, goes direct to dim."""
    # Areas are loaded directly into dim_cpi_area (small, stable dataset)
    return len(rows)


# ---------------------------------------------------------------------------
# Dimension loaders
# ---------------------------------------------------------------------------


def load_dim_cpi_member(
    conn: duckdb.DuckDBPyConnection,
    items: list[CpiItemRow],
    source_version: str,
) -> int:
    """Load dim_cpi_member from parsed item hierarchy.

    Classifies semantic_role and is_cross_cutting for each member.
    Idempotent: skips if source_version already loaded.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchone()[0]
    if existing > 0:
        return 0

    batch = []
    for item in items:
        role = _classify_semantic_role(item.item_code)
        is_cross = role in ("special_aggregate", "purchasing_power")
        has_avg_price = item.item_code.startswith("SS")
        batch.append(
            (
                item.item_code,
                item.item_name,
                item.hierarchy_level,
                role,
                is_cross,
                has_avg_price,
                True,
                str(item.display_level),
                source_version,
            )
        )

    if batch:
        conn.executemany(
            """INSERT INTO dim_cpi_member
                (member_code, title, hierarchy_level, semantic_role,
                 is_cross_cutting, has_average_price, has_relative_importance,
                 publication_depth, source_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_bridge_cpi_member_hierarchy(
    conn: duckdb.DuckDBPyConnection,
    items: list[CpiItemRow],
    source_version: str,
) -> int:
    """Load bridge_cpi_member_hierarchy from parsed items with parent edges.

    Uses parent_item_code inferred by the parser.
    Idempotent: skips if source_version already loaded.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_cpi_member_hierarchy WHERE source_version = ?",
        [source_version],
    ).fetchone()[0]
    if existing > 0:
        return 0

    # Build code → member_key lookup
    key_map: dict[str, int] = {}
    for row in conn.execute(
        "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchall():
        key_map[row[0]] = row[1]

    batch = []
    for item in items:
        if item.parent_item_code is None:
            continue
        parent_key = key_map.get(item.parent_item_code)
        child_key = key_map.get(item.item_code)
        if parent_key is None or child_key is None:
            continue
        batch.append((parent_key, child_key, 1, source_version))

    if batch:
        conn.executemany(
            """INSERT INTO bridge_cpi_member_hierarchy
                (parent_member_key, child_member_key, hierarchy_depth, source_version)
                VALUES (?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_bridge_cpi_member_relation(
    conn: duckdb.DuckDBPyConnection,
    items: list[CpiItemRow],
    source_version: str,
) -> int:
    """Load bridge_cpi_member_relation for cross-cutting analytical relationships.

    Creates relation entries linking special aggregates to their conceptual anchors.
    Idempotent: skips if source_version already loaded.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_cpi_member_relation WHERE source_version = ?",
        [source_version],
    ).fetchone()[0]
    if existing > 0:
        return 0

    # Build code → member_key lookup
    key_map: dict[str, int] = {}
    for row in conn.execute(
        "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchall():
        key_map[row[0]] = row[1]

    # Define known cross-cutting relationships
    # (aggregate_code, anchor_code, relation_type, description)
    relations = [
        ("SA0L1", "SA0", "core_aggregate", "All items less food"),
        ("SA0L1E", "SA0", "core_aggregate", "All items less food and energy"),
        ("SA0E", "SA0", "energy", "Energy items"),
        ("SAE", "SA0", "energy", "Energy"),
        ("SAC", "SA0", "commodities", "Commodities"),
        ("SAS", "SA0", "services", "Services"),
        ("SA0R", "SA0", "purchasing_power", "Purchasing power of consumer dollar"),
    ]

    batch = []
    for agg_code, anchor_code, rel_type, desc in relations:
        key_a = key_map.get(agg_code)
        key_b = key_map.get(anchor_code)
        if key_a is None or key_b is None:
            continue
        batch.append((key_a, key_b, rel_type, desc, source_version))

    if batch:
        conn.executemany(
            """INSERT INTO bridge_cpi_member_relation
                (member_key_a, member_key_b, relation_type, description, source_version)
                VALUES (?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_dim_cpi_area(
    conn: duckdb.DuckDBPyConnection,
    areas: list[CpiAreaRow],
    source_version: str,
) -> int:
    """Load dim_cpi_area from parsed area definitions.

    Idempotent: skips if source_version already loaded.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM dim_cpi_area WHERE source_version = ?",
        [source_version],
    ).fetchone()[0]
    if existing > 0:
        return 0

    batch = [
        (
            area.area_code,
            area.area_title,
            area.area_type,
            _classify_publication_frequency(area.area_code),
            source_version,
        )
        for area in areas
    ]
    if batch:
        conn.executemany(
            """INSERT INTO dim_cpi_area
                (area_code, area_title, area_type, publication_frequency, source_version)
                VALUES (?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_bridge_cpi_area_hierarchy(
    conn: duckdb.DuckDBPyConnection,
    areas: list[CpiAreaRow],
    source_version: str,
) -> int:
    """Load bridge_cpi_area_hierarchy from area display_level ordering.

    The area hierarchy: national → region → division → metro/size_class.
    Inferred from display_level the same way items are.
    Idempotent: skips if source_version already loaded.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_cpi_area_hierarchy WHERE source_version = ?",
        [source_version],
    ).fetchone()[0]
    if existing > 0:
        return 0

    # Build code → area_key lookup
    key_map: dict[str, int] = {}
    for row in conn.execute(
        "SELECT area_code, area_key FROM dim_cpi_area WHERE source_version = ?",
        [source_version],
    ).fetchall():
        key_map[row[0]] = row[1]

    # Infer parent-child from display_level ordering
    from jobclass.parse.cpi_domain import _infer_parents

    area_levels = [(a.area_code, a.display_level) for a in areas]
    parent_map = _infer_parents(area_levels)

    batch = []
    for area in areas:
        parent_code = parent_map.get(area.area_code)
        if parent_code is None:
            continue
        parent_key = key_map.get(parent_code)
        child_key = key_map.get(area.area_code)
        if parent_key is None or child_key is None:
            continue
        batch.append((parent_key, child_key, source_version))

    if batch:
        conn.executemany(
            """INSERT INTO bridge_cpi_area_hierarchy
                (parent_area_key, child_area_key, source_version)
                VALUES (?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_dim_cpi_series_variant(
    conn: duckdb.DuckDBPyConnection,
    series: list[CpiSeriesRow],
    source_version: str,
) -> int:
    """Load dim_cpi_series_variant from parsed series metadata.

    Links each variant to member_key and area_key via code lookups.
    Idempotent: skips if source_version already loaded.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM dim_cpi_series_variant WHERE source_version = ?",
        [source_version],
    ).fetchone()[0]
    if existing > 0:
        return 0

    # Build lookup maps
    member_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchall():
        member_keys[row[0]] = row[1]

    area_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT area_code, area_key FROM dim_cpi_area WHERE source_version = ?",
        [source_version],
    ).fetchall():
        area_keys[row[0]] = row[1]

    batch = [
        (
            s.series_id,
            "CPI-U",
            s.seasonal_adjustment,
            s.periodicity,
            s.area_code,
            s.item_code,
            member_keys.get(s.item_code),
            area_keys.get(s.area_code),
            source_version,
        )
        for s in series
    ]
    if batch:
        conn.executemany(
            """INSERT INTO dim_cpi_series_variant
                (series_id, index_family, seasonal_adjustment, periodicity,
                 area_code, item_code, member_key, area_key, source_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_fact_cpi_observation(
    conn: duckdb.DuckDBPyConnection,
    observations: list[CpiObservationRow],
    source_version: str,
    source_release_id: str,
) -> int:
    """Load fact_cpi_observation from parsed observation rows.

    Joins against dim_cpi_series_variant to resolve variant_key, member_key,
    and area_key. Skips observations with no matching variant or time period.
    Idempotent via unique grain index (variant_key × time_period_key).
    """
    # Build series_id → variant info lookup
    variant_info: dict[str, tuple[int, int, int]] = {}  # series_id → (variant_key, member_key, area_key)
    for row in conn.execute(
        """SELECT series_id, variant_key, member_key, area_key
           FROM dim_cpi_series_variant
           WHERE source_version = ?""",
        [source_version],
    ).fetchall():
        if row[2] is not None and row[3] is not None:
            variant_info[row[0]] = (row[1], row[2], row[3])

    # Build (year, period) → period_key lookup for monthly periods
    # CPI uses monthly periods: M01-M12 plus M13 (annual average)
    period_keys: dict[tuple[int, str], int] = {}
    for row in conn.execute("SELECT period_key, year, period_type FROM dim_time_period").fetchall():
        if row[2] == "annual":
            period_keys[(row[1], "M13")] = row[0]

    # Build existing grain set for idempotency check
    existing_grains: set[tuple[int, int]] = set()
    for row in conn.execute("SELECT variant_key, time_period_key FROM fact_cpi_observation").fetchall():
        existing_grains.add((row[0], row[1]))

    # Collect batch of rows to insert
    batch = []
    for obs in observations:
        info = variant_info.get(obs.series_id)
        if info is None:
            continue
        variant_key, member_key, area_key = info
        period_key = period_keys.get((obs.year, obs.period))
        if period_key is None:
            continue
        if (variant_key, period_key) in existing_grains:
            continue
        batch.append((member_key, area_key, variant_key, period_key, obs.value, source_release_id))
        existing_grains.add((variant_key, period_key))

    if batch:
        conn.executemany(
            """INSERT INTO fact_cpi_observation
                (member_key, area_key, variant_key, time_period_key,
                 index_value, source_release_id)
                VALUES (?, ?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_fact_cpi_relative_importance(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiRelativeImportanceRow],
    source_version: str,
    source_release_id: str,
) -> int:
    """Load fact_cpi_relative_importance from parsed relative importance rows.

    Resolves member_key and area_key via dimension lookups.
    Idempotent via unique grain (member_key × area_key × reference_period).
    """
    if not rows:
        return 0

    # Build lookup maps
    member_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchall():
        member_keys[row[0]] = row[1]

    area_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT area_code, area_key FROM dim_cpi_area WHERE source_version = ?",
        [source_version],
    ).fetchall():
        area_keys[row[0]] = row[1]

    # Build existing grain set for idempotency
    existing_grains: set[tuple[int, int, str]] = set()
    for row in conn.execute(
        "SELECT member_key, area_key, reference_period FROM fact_cpi_relative_importance"
    ).fetchall():
        existing_grains.add((row[0], row[1], row[2]))

    batch = []
    for ri in rows:
        member_key = member_keys.get(ri.item_code)
        area_key = area_keys.get(ri.area_code)
        if member_key is None or area_key is None:
            continue
        if (member_key, area_key, ri.reference_period) in existing_grains:
            continue
        batch.append((member_key, area_key, ri.reference_period, ri.relative_importance, source_release_id))
        existing_grains.add((member_key, area_key, ri.reference_period))

    if batch:
        conn.executemany(
            """INSERT INTO fact_cpi_relative_importance
                (member_key, area_key, reference_period,
                 relative_importance_value, source_release_id)
                VALUES (?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_fact_cpi_average_price(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiAveragePriceRow],
    source_version: str,
    source_release_id: str,
) -> int:
    """Load fact_cpi_average_price from parsed average price rows.

    Resolves member_key and area_key via dimension lookups.
    Idempotent via unique grain (member_key × area_key × time_period_key).
    """
    if not rows:
        return 0

    # Build lookup maps
    member_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchall():
        member_keys[row[0]] = row[1]

    area_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT area_code, area_key FROM dim_cpi_area WHERE source_version = ?",
        [source_version],
    ).fetchall():
        area_keys[row[0]] = row[1]

    # Build (year, period) → period_key lookup
    period_keys: dict[tuple[int, str], int] = {}
    for row in conn.execute("SELECT period_key, year, period_type FROM dim_time_period").fetchall():
        if row[2] == "annual":
            period_keys[(row[1], "M13")] = row[0]

    # Build existing grain set for idempotency
    existing_grains: set[tuple[int, int, int]] = set()
    for row in conn.execute("SELECT member_key, area_key, time_period_key FROM fact_cpi_average_price").fetchall():
        existing_grains.add((row[0], row[1], row[2]))

    batch = []
    for ap in rows:
        member_key = member_keys.get(ap.item_code)
        area_key = area_keys.get(ap.area_code)
        if member_key is None or area_key is None:
            continue
        period_key = period_keys.get((ap.year, ap.period))
        if period_key is None:
            continue
        if (member_key, area_key, period_key) in existing_grains:
            continue
        batch.append((member_key, area_key, period_key, ap.average_price, None, source_release_id))
        existing_grains.add((member_key, area_key, period_key))

    if batch:
        conn.executemany(
            """INSERT INTO fact_cpi_average_price
                (member_key, area_key, time_period_key,
                 average_price, unit_description, source_release_id)
                VALUES (?, ?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_fact_cpi_revision_vintage(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiRevisionVintageRow],
    source_version: str,
    source_release_id: str,
) -> int:
    """Load fact_cpi_revision_vintage for C-CPI-U preliminary/revised values.

    Tracks how C-CPI-U index values evolve from preliminary to final as BLS
    revises estimates over a 10-12 month window.

    Grain: member × area × time_period × vintage_label.
    Idempotent via in-memory grain set.
    """
    if not rows:
        return 0

    # Build lookup maps
    member_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
        [source_version],
    ).fetchall():
        member_keys[row[0]] = row[1]

    area_keys: dict[str, int] = {}
    for row in conn.execute(
        "SELECT area_code, area_key FROM dim_cpi_area WHERE source_version = ?",
        [source_version],
    ).fetchall():
        area_keys[row[0]] = row[1]

    # Build (year, period) → period_key lookup
    period_keys: dict[tuple[int, str], int] = {}
    for row in conn.execute("SELECT period_key, year, period_type FROM dim_time_period").fetchall():
        if row[2] == "annual":
            period_keys[(row[1], "M13")] = row[0]

    # Build existing grain set for idempotency
    existing_grains: set[tuple[int, int, int, str]] = set()
    for row in conn.execute(
        "SELECT member_key, area_key, time_period_key, vintage_label FROM fact_cpi_revision_vintage"
    ).fetchall():
        existing_grains.add((row[0], row[1], row[2], row[3]))

    batch = []
    for rv in rows:
        member_key = member_keys.get(rv.item_code)
        area_key = area_keys.get(rv.area_code)
        if member_key is None or area_key is None:
            continue
        period_key = period_keys.get((rv.year, rv.period))
        if period_key is None:
            continue
        grain = (member_key, area_key, period_key, rv.vintage_label)
        if grain in existing_grains:
            continue
        batch.append(
            (
                member_key,
                area_key,
                period_key,
                rv.vintage_label,
                rv.index_value,
                rv.is_preliminary,
                None,
                source_release_id,
            )
        )
        existing_grains.add(grain)

    if batch:
        conn.executemany(
            """INSERT INTO fact_cpi_revision_vintage
                (member_key, area_key, time_period_key, vintage_label,
                 index_value, is_preliminary, revision_date, source_release_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
    return len(batch)


def load_cpi_overlay_members(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiOverlaySeriesRow],
    source_version: str,
) -> int:
    """Load overlay members into dim_cpi_member and bridge_cpi_member_relation.

    Overlay members (Cleveland Fed median CPI, trimmed-mean CPI, FRED mirrors) are
    loaded with semantic_role = 'external_overlay' and linked to SA0 via
    bridge_cpi_member_relation (relation_type matching overlay_source).

    Idempotent: skips if member_code already exists for this source_version.
    """
    if not rows:
        return 0

    # Deduplicate overlay members from rows
    overlay_members: dict[str, tuple[str, str]] = {}
    for r in rows:
        if r.member_code not in overlay_members:
            overlay_members[r.member_code] = (r.title, r.overlay_source)

    # Check existing member codes
    existing_codes: set[str] = {
        r[0]
        for r in conn.execute(
            "SELECT member_code FROM dim_cpi_member WHERE source_version = ?",
            [source_version],
        ).fetchall()
    }

    new_members = []
    for code, (title, _source) in overlay_members.items():
        if code not in existing_codes:
            new_members.append(
                (
                    code,
                    title,
                    "external_overlay",
                    "external_overlay",
                    False,
                    False,
                    False,
                    "overlay",
                    source_version,
                )
            )

    if new_members:
        conn.executemany(
            """INSERT INTO dim_cpi_member
                (member_code, title, hierarchy_level, semantic_role,
                 is_cross_cutting, has_average_price, has_relative_importance,
                 publication_depth, source_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            new_members,
        )

    # Link overlays to SA0 via bridge_cpi_member_relation
    sa0_key = conn.execute(
        "SELECT member_key FROM dim_cpi_member WHERE member_code = 'SA0' AND source_version = ?",
        [source_version],
    ).fetchone()
    if sa0_key:
        key_map: dict[str, int] = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT member_code, member_key FROM dim_cpi_member WHERE source_version = ?",
                [source_version],
            ).fetchall()
        }
        for code, (title, source) in overlay_members.items():
            member_key = key_map.get(code)
            if member_key is None:
                continue
            # Check if relation already exists
            exists = conn.execute(
                """SELECT 1 FROM bridge_cpi_member_relation
                   WHERE member_key_a = ? AND member_key_b = ? AND source_version = ?""",
                [member_key, sa0_key[0], source_version],
            ).fetchone()
            if not exists:
                conn.execute(
                    """INSERT INTO bridge_cpi_member_relation
                        (member_key_a, member_key_b, relation_type, description, source_version)
                        VALUES (?, ?, ?, ?, ?)""",
                    [member_key, sa0_key[0], source, f"{title} overlay of All Items", source_version],
                )

    return len(new_members)
