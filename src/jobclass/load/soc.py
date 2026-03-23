"""SOC staging and warehouse loaders."""

import duckdb

from jobclass.parse.soc import SocDefinitionRow, SocHierarchyRow


def load_soc_hierarchy_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[SocHierarchyRow],
    source_release_id: str,
) -> int:
    """Load parsed SOC hierarchy rows into stage__soc__hierarchy.

    Clears existing rows for the same source_release_id first (idempotent).
    Returns count of rows loaded.
    """
    conn.execute("DELETE FROM stage__soc__hierarchy WHERE source_release_id = ?", [source_release_id])

    for row in rows:
        conn.execute(
            """INSERT INTO stage__soc__hierarchy
            (soc_code, occupation_title, occupation_level, occupation_level_name,
             parent_soc_code, source_release_id, parser_version)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [row.soc_code, row.occupation_title, row.occupation_level,
             row.occupation_level_name, row.parent_soc_code,
             row.source_release_id, row.parser_version],
        )
    return len(rows)


def load_soc_definitions_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[SocDefinitionRow],
    source_release_id: str,
) -> int:
    """Load parsed SOC definition rows into stage__soc__definitions.

    Clears existing rows for the same source_release_id first (idempotent).
    Returns count of rows loaded.
    """
    conn.execute("DELETE FROM stage__soc__definitions WHERE source_release_id = ?", [source_release_id])

    for row in rows:
        conn.execute(
            """INSERT INTO stage__soc__definitions
            (soc_code, occupation_definition, source_release_id, parser_version)
            VALUES (?, ?, ?, ?)""",
            [row.soc_code, row.occupation_definition, row.source_release_id, row.parser_version],
        )
    return len(rows)


def _derive_group_codes(soc_code: str, level: int) -> dict:
    """Derive major/minor/broad/detailed group codes from a SOC code."""
    prefix, suffix = soc_code.split("-")
    result = {
        "major_group_code": f"{prefix}-0000",
        "minor_group_code": None,
        "broad_occupation_code": None,
        "detailed_occupation_code": None,
    }
    if level >= 2:
        result["minor_group_code"] = f"{prefix}-{suffix[0]}000"
    if level >= 3:
        result["broad_occupation_code"] = f"{prefix}-{suffix[:3]}0"
    if level >= 4:
        result["detailed_occupation_code"] = soc_code
    return result


def load_dim_occupation(
    conn: duckdb.DuckDBPyConnection,
    soc_version: str,
    source_release_id: str,
) -> int:
    """Load dim_occupation from staging tables.

    Version-aware: inserts new rows for new soc_version without mutating prior versions.
    Returns count of rows loaded.
    """
    # Check if this version already loaded
    existing = conn.execute(
        "SELECT COUNT(*) FROM dim_occupation WHERE soc_version = ?",
        [soc_version],
    ).fetchone()[0]
    if existing > 0:
        return 0  # Idempotent: already loaded

    # Get hierarchy and definitions from staging
    hierarchy = conn.execute(
        "SELECT * FROM stage__soc__hierarchy WHERE source_release_id = ?",
        [source_release_id],
    ).fetchall()
    h_cols = [d[0] for d in conn.description]

    definitions = {}
    for row in conn.execute(
        "SELECT soc_code, occupation_definition FROM stage__soc__definitions WHERE source_release_id = ?",
        [source_release_id],
    ).fetchall():
        definitions[row[0]] = row[1]

    # Determine leaf codes (detailed occupations or codes with no children)
    all_codes = set()
    parent_codes = set()
    for row in hierarchy:
        h = dict(zip(h_cols, row))
        all_codes.add(h["soc_code"])
        if h["parent_soc_code"]:
            parent_codes.add(h["parent_soc_code"])
    leaf_codes = all_codes - parent_codes

    loaded = 0
    for row in hierarchy:
        h = dict(zip(h_cols, row))
        groups = _derive_group_codes(h["soc_code"], h["occupation_level"])
        is_leaf = h["soc_code"] in leaf_codes

        key = conn.execute("SELECT nextval('seq_occupation_key')").fetchone()[0]
        conn.execute(
            """INSERT INTO dim_occupation
            (occupation_key, soc_code, occupation_title, occupation_level,
             occupation_level_name, parent_soc_code, major_group_code,
             minor_group_code, broad_occupation_code, detailed_occupation_code,
             occupation_definition, soc_version, is_leaf,
             is_current, source_release_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [key, h["soc_code"], h["occupation_title"], h["occupation_level"],
             h["occupation_level_name"], h["parent_soc_code"],
             groups["major_group_code"], groups["minor_group_code"],
             groups["broad_occupation_code"], groups["detailed_occupation_code"],
             definitions.get(h["soc_code"]),
             soc_version, is_leaf, True, source_release_id],
        )
        loaded += 1

    return loaded


def load_bridge_occupation_hierarchy(
    conn: duckdb.DuckDBPyConnection,
    soc_version: str,
    source_release_id: str,
) -> int:
    """Load bridge_occupation_hierarchy from dim_occupation.

    Creates parent-child relationships for the specified SOC version.
    Returns count of rows loaded.
    """
    # Check if already loaded
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_occupation_hierarchy WHERE soc_version = ?",
        [soc_version],
    ).fetchone()[0]
    if existing > 0:
        return 0  # Idempotent

    # Build lookup: soc_code -> occupation_key
    key_map = {}
    for row in conn.execute(
        "SELECT soc_code, occupation_key FROM dim_occupation WHERE soc_version = ?",
        [soc_version],
    ).fetchall():
        key_map[row[0]] = row[1]

    loaded = 0
    for row in conn.execute(
        """SELECT occupation_key, soc_code, parent_soc_code, occupation_level
           FROM dim_occupation
           WHERE soc_version = ? AND parent_soc_code IS NOT NULL""",
        [soc_version],
    ).fetchall():
        child_key, child_code, parent_code, level = row
        parent_key = key_map.get(parent_code)
        if parent_key is None:
            continue

        conn.execute(
            """INSERT INTO bridge_occupation_hierarchy
            (parent_occupation_key, child_occupation_key, relationship_level,
             soc_version, source_release_id)
            VALUES (?, ?, ?, ?, ?)""",
            [parent_key, child_key, level, soc_version, source_release_id],
        )
        loaded += 1

    return loaded
