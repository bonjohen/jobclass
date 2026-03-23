"""SOC-specific validations: structural and semantic."""

from dataclasses import dataclass

import duckdb


@dataclass
class ValidationResult:
    passed: bool
    check_name: str
    message: str
    details: dict | None = None


def validate_soc_structural(conn: duckdb.DuckDBPyConnection, source_release_id: str) -> list[ValidationResult]:
    """Structural validations for SOC staging tables."""
    results = []

    # Required columns check
    for table, required_cols in [
        ("stage__soc__hierarchy", ["soc_code", "occupation_title", "occupation_level", "occupation_level_name", "parent_soc_code", "source_release_id", "parser_version"]),
        ("stage__soc__definitions", ["soc_code", "occupation_definition", "source_release_id", "parser_version"]),
    ]:
        actual_cols = {row[0] for row in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name = ?", [table]).fetchall()}
        missing = set(required_cols) - actual_cols
        results.append(ValidationResult(
            passed=len(missing) == 0,
            check_name=f"{table}_required_columns",
            message=f"Missing columns: {missing}" if missing else "All required columns present",
        ))

    # Minimum row count
    h_count = conn.execute(
        "SELECT COUNT(*) FROM stage__soc__hierarchy WHERE source_release_id = ?",
        [source_release_id],
    ).fetchone()[0]
    results.append(ValidationResult(
        passed=h_count >= 5,
        check_name="hierarchy_min_row_count",
        message=f"Row count: {h_count}",
        details={"row_count": h_count, "minimum": 5},
    ))

    # Grain uniqueness: soc_code + source_release_id
    dups = conn.execute(
        """SELECT soc_code, COUNT(*) as cnt
           FROM stage__soc__hierarchy
           WHERE source_release_id = ?
           GROUP BY soc_code HAVING cnt > 1""",
        [source_release_id],
    ).fetchall()
    results.append(ValidationResult(
        passed=len(dups) == 0,
        check_name="hierarchy_grain_uniqueness",
        message=f"{len(dups)} duplicate keys found" if dups else "No duplicate keys",
        details={"duplicates": [r[0] for r in dups]} if dups else None,
    ))

    return results


def validate_soc_hierarchy_completeness(conn: duckdb.DuckDBPyConnection, source_release_id: str) -> ValidationResult:
    """Semantic validation: every leaf has a path to its major group."""
    # Get all leaf codes (detailed occupations)
    leaves = conn.execute(
        """SELECT h.soc_code, h.parent_soc_code
           FROM stage__soc__hierarchy h
           WHERE h.source_release_id = ?
             AND h.occupation_level = 4""",
        [source_release_id],
    ).fetchall()

    # Build parent lookup
    parent_map = {}
    level_map = {}
    for row in conn.execute(
        "SELECT soc_code, parent_soc_code, occupation_level FROM stage__soc__hierarchy WHERE source_release_id = ?",
        [source_release_id],
    ).fetchall():
        parent_map[row[0]] = row[1]
        level_map[row[0]] = row[2]

    orphans = []
    for leaf_code, _ in leaves:
        current = leaf_code
        found_major = False
        visited = set()
        while current and current not in visited:
            visited.add(current)
            if level_map.get(current) == 1:
                found_major = True
                break
            current = parent_map.get(current)
        if not found_major:
            orphans.append(leaf_code)

    return ValidationResult(
        passed=len(orphans) == 0,
        check_name="hierarchy_completeness",
        message=f"{len(orphans)} leaves without path to major group" if orphans else "All leaves reach major group",
        details={"orphan_leaves": orphans} if orphans else None,
    )
