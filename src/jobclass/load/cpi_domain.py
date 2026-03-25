"""CPI domain expansion loaders.

Loads parsed CPI data into warehouse dimensions, bridges, and facts.
The existing cpi.py handles the single-series deflator. This module
handles the full CPI analytical domain.
"""

from __future__ import annotations

import duckdb

from jobclass.parse.cpi_domain import (
    CpiAreaRow,
    CpiItemRow,
    CpiObservationRow,
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
    for r in rows:
        conn.execute(
            """INSERT INTO stage__bls__cpi_item_hierarchy
                (item_code, item_name, hierarchy_level, parent_item_code,
                 sort_sequence, selectable, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.item_code, r.item_name, r.hierarchy_level, r.parent_item_code,
                r.sort_sequence, r.selectable, source_release_id, r.parser_version,
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
    for r in rows:
        conn.execute(
            """INSERT INTO stage__bls__cpi_series
                (series_id, index_family, seasonal_adjustment, periodicity,
                 area_code, item_code, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.series_id, "CPI-U", r.seasonal_adjustment, r.periodicity,
                r.area_code, r.item_code, source_release_id, r.parser_version,
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

    loaded = 0
    for item in items:
        role = _classify_semantic_role(item.item_code)
        is_cross = role in ("special_aggregate", "purchasing_power")
        has_avg_price = item.item_code.startswith("SS")

        conn.execute(
            """INSERT INTO dim_cpi_member
                (member_code, title, hierarchy_level, semantic_role,
                 is_cross_cutting, has_average_price, has_relative_importance,
                 publication_depth, source_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                item.item_code,
                item.item_name,
                item.hierarchy_level,
                role,
                is_cross,
                has_avg_price,
                True,  # Most items have relative importance data
                str(item.display_level),
                source_version,
            ],
        )
        loaded += 1
    return loaded


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

    loaded = 0
    for item in items:
        if item.parent_item_code is None:
            continue
        parent_key = key_map.get(item.parent_item_code)
        child_key = key_map.get(item.item_code)
        if parent_key is None or child_key is None:
            continue

        conn.execute(
            """INSERT INTO bridge_cpi_member_hierarchy
                (parent_member_key, child_member_key, hierarchy_depth, source_version)
                VALUES (?, ?, ?, ?)""",
            [parent_key, child_key, 1, source_version],
        )
        loaded += 1
    return loaded


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

    loaded = 0
    for agg_code, anchor_code, rel_type, desc in relations:
        key_a = key_map.get(agg_code)
        key_b = key_map.get(anchor_code)
        if key_a is None or key_b is None:
            continue
        conn.execute(
            """INSERT INTO bridge_cpi_member_relation
                (member_key_a, member_key_b, relation_type, description, source_version)
                VALUES (?, ?, ?, ?, ?)""",
            [key_a, key_b, rel_type, desc, source_version],
        )
        loaded += 1
    return loaded


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

    loaded = 0
    for area in areas:
        pub_freq = _classify_publication_frequency(area.area_code)
        conn.execute(
            """INSERT INTO dim_cpi_area
                (area_code, area_title, area_type, publication_frequency, source_version)
                VALUES (?, ?, ?, ?, ?)""",
            [area.area_code, area.area_title, area.area_type, pub_freq, source_version],
        )
        loaded += 1
    return loaded


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

    loaded = 0
    for area in areas:
        parent_code = parent_map.get(area.area_code)
        if parent_code is None:
            continue
        parent_key = key_map.get(parent_code)
        child_key = key_map.get(area.area_code)
        if parent_key is None or child_key is None:
            continue
        conn.execute(
            """INSERT INTO bridge_cpi_area_hierarchy
                (parent_area_key, child_area_key, source_version)
                VALUES (?, ?, ?)""",
            [parent_key, child_key, source_version],
        )
        loaded += 1
    return loaded


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

    loaded = 0
    for s in series:
        member_key = member_keys.get(s.item_code)
        area_key = area_keys.get(s.area_code)

        conn.execute(
            """INSERT INTO dim_cpi_series_variant
                (series_id, index_family, seasonal_adjustment, periodicity,
                 area_code, item_code, member_key, area_key, source_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                s.series_id, "CPI-U", s.seasonal_adjustment, s.periodicity,
                s.area_code, s.item_code, member_key, area_key, source_version,
            ],
        )
        loaded += 1
    return loaded


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
    for row in conn.execute(
        "SELECT period_key, year, period_type FROM dim_time_period"
    ).fetchall():
        if row[2] == "annual":
            period_keys[(row[1], "M13")] = row[0]

    loaded = 0
    skipped = 0
    for obs in observations:
        info = variant_info.get(obs.series_id)
        if info is None:
            skipped += 1
            continue

        variant_key, member_key, area_key = info

        # Look up time period — for now, only annual averages (M13)
        period_key_tuple = (obs.year, obs.period)
        period_key = period_keys.get(period_key_tuple)
        if period_key is None:
            skipped += 1
            continue

        # Idempotent: skip if grain already exists
        exists = conn.execute(
            """SELECT 1 FROM fact_cpi_observation
               WHERE variant_key = ? AND time_period_key = ?""",
            [variant_key, period_key],
        ).fetchone()
        if exists:
            continue

        conn.execute(
            """INSERT INTO fact_cpi_observation
                (member_key, area_key, variant_key, time_period_key,
                 index_value, source_release_id)
                VALUES (?, ?, ?, ?, ?, ?)""",
            [member_key, area_key, variant_key, period_key, obs.value, source_release_id],
        )
        loaded += 1

    return loaded
