"""O*NET staging and warehouse loaders."""

from __future__ import annotations

import duckdb

from jobclass.load import _safe_identifier
from jobclass.parse.onet import OnetDescriptorRow, OnetEducationRow, OnetTaskRow, OnetTechnologyRow


def load_onet_descriptor_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[OnetDescriptorRow],
    table_name: str,
    source_release_id: str,
) -> None:
    """Load parsed O*NET descriptor rows (skills/knowledge/abilities) into staging.

    Idempotent: deletes existing rows for this release before inserting.
    """
    table_name = _safe_identifier(table_name)
    conn.execute(f"DELETE FROM {table_name} WHERE source_release_id = ?", [source_release_id])
    for r in rows:
        conn.execute(
            f"""INSERT INTO {table_name}
                (occupation_code, element_id, element_name, scale_id, data_value,
                 n, standard_error, lower_ci, upper_ci, recommend_suppress,
                 not_relevant, date, domain_source, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.occupation_code,
                r.element_id,
                r.element_name,
                r.scale_id,
                r.data_value,
                r.n,
                r.standard_error,
                r.lower_ci,
                r.upper_ci,
                r.recommend_suppress,
                r.not_relevant,
                r.date,
                r.domain_source,
                r.source_release_id,
                r.parser_version,
            ],
        )


def load_onet_task_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[OnetTaskRow],
    source_release_id: str,
) -> None:
    """Load parsed O*NET task rows into staging.

    Idempotent: deletes existing rows for this release before inserting.
    """
    conn.execute("DELETE FROM stage__onet__tasks WHERE source_release_id = ?", [source_release_id])
    for r in rows:
        conn.execute(
            """INSERT INTO stage__onet__tasks
               (occupation_code, task_id, task, task_type, incumbents_responding,
                date, domain_source, source_release_id, parser_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.occupation_code,
                r.task_id,
                r.task,
                r.task_type,
                r.incumbents_responding,
                r.date,
                r.domain_source,
                r.source_release_id,
                r.parser_version,
            ],
        )


def load_dim_descriptor(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    key_column: str,
    staging_table: str,
    source_version: str,
) -> None:
    """Load a descriptor dimension (dim_skill, dim_knowledge, dim_ability) from staging.

    Inserts distinct element_id + element_name pairs not already present for this version.
    """
    table_name = _safe_identifier(table_name)
    staging_table = _safe_identifier(staging_table)
    conn.execute(
        f"""INSERT INTO {table_name} (element_id, element_name, source_version)
            SELECT DISTINCT s.element_id, s.element_name, ?
            FROM {staging_table} s
            WHERE NOT EXISTS (
                SELECT 1 FROM {table_name} d
                WHERE d.element_id = s.element_id AND d.source_version = ?
            )""",
        [source_version, source_version],
    )


def load_dim_task(
    conn: duckdb.DuckDBPyConnection,
    source_version: str,
) -> None:
    """Load dim_task from staging. Inserts new task_id values not already present for this version."""
    conn.execute(
        """INSERT INTO dim_task (task_id, task, task_type, source_version)
           SELECT DISTINCT s.task_id, s.task, s.task_type, ?
           FROM stage__onet__tasks s
           WHERE NOT EXISTS (
               SELECT 1 FROM dim_task d
               WHERE d.task_id = s.task_id AND d.source_version = ?
           )""",
        [source_version, source_version],
    )


def load_bridge_occupation_descriptor(
    conn: duckdb.DuckDBPyConnection,
    bridge_table: str,
    dim_table: str,
    dim_key_column: str,
    staging_table: str,
    source_version: str,
    source_release_id: str,
    soc_version: str,
) -> None:
    """Load a bridge table (occupation ↔ descriptor) from staging.

    Idempotent: skips if rows already exist for this source_version + source_release_id.
    """
    bridge_table = _safe_identifier(bridge_table)
    dim_table = _safe_identifier(dim_table)
    dim_key_column = _safe_identifier(dim_key_column)
    staging_table = _safe_identifier(staging_table)
    existing = conn.execute(
        f"SELECT COUNT(*) FROM {bridge_table} WHERE source_version = ? AND source_release_id = ?",
        [source_version, source_release_id],
    ).fetchone()[0]
    if existing > 0:
        return

    conn.execute(
        f"""INSERT INTO {bridge_table}
            (occupation_key, {dim_key_column}, scale_id, data_value, n, source_version, source_release_id)
            SELECT o.occupation_key, d.{dim_key_column}, s.scale_id, s.data_value, s.n, ?, ?
            FROM {staging_table} s
            JOIN dim_occupation o ON o.soc_code = s.occupation_code AND o.soc_version = ?
            JOIN {dim_table} d ON d.element_id = s.element_id AND d.source_version = ?
            WHERE s.source_release_id = ?""",
        [source_version, source_release_id, soc_version, source_version, source_release_id],
    )


def load_bridge_occupation_task(
    conn: duckdb.DuckDBPyConnection,
    source_version: str,
    source_release_id: str,
    soc_version: str,
) -> None:
    """Load bridge_occupation_task from staging.

    Idempotent: skips if rows already exist for this source_version + source_release_id.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_occupation_task WHERE source_version = ? AND source_release_id = ?",
        [source_version, source_release_id],
    ).fetchone()[0]
    if existing > 0:
        return

    conn.execute(
        """INSERT INTO bridge_occupation_task
           (occupation_key, task_key, data_value, n, source_version, source_release_id)
           SELECT o.occupation_key, d.task_key, NULL, s.incumbents_responding, ?, ?
           FROM stage__onet__tasks s
           JOIN dim_occupation o ON o.soc_code = s.occupation_code AND o.soc_version = ?
           JOIN dim_task d ON d.task_id = s.task_id AND d.source_version = ?
           WHERE s.source_release_id = ?""",
        [source_version, source_release_id, soc_version, source_version, source_release_id],
    )


def load_onet_education_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[OnetEducationRow],
    source_release_id: str,
) -> None:
    """Load parsed O*NET education rows into staging.

    Idempotent: deletes existing rows for this release before inserting.
    """
    conn.execute("DELETE FROM stage__onet__education WHERE source_release_id = ?", [source_release_id])
    for r in rows:
        conn.execute(
            """INSERT INTO stage__onet__education
                (occupation_code, element_id, element_name, scale_id, category,
                 data_value, n, standard_error, lower_ci, upper_ci,
                 recommend_suppress, not_relevant, date, domain_source,
                 source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.occupation_code,
                r.element_id,
                r.element_name,
                r.scale_id,
                r.category,
                r.data_value,
                r.n,
                r.standard_error,
                r.lower_ci,
                r.upper_ci,
                r.recommend_suppress,
                r.not_relevant,
                r.date,
                r.domain_source,
                r.source_release_id,
                r.parser_version,
            ],
        )


def load_dim_education_requirement(
    conn: duckdb.DuckDBPyConnection,
    source_version: str,
) -> None:
    """Load dim_education_requirement from staging.

    Inserts distinct (element_id, scale_id, category) triples not already present.
    """
    conn.execute(
        """INSERT INTO dim_education_requirement
            (element_id, element_name, scale_id, category, category_label, source_version)
            SELECT DISTINCT s.element_id, s.element_name, s.scale_id, s.category, NULL, ?
            FROM stage__onet__education s
            WHERE NOT EXISTS (
                SELECT 1 FROM dim_education_requirement d
                WHERE d.element_id = s.element_id
                  AND d.scale_id = s.scale_id
                  AND d.category = s.category
                  AND d.source_version = ?
            )""",
        [source_version, source_version],
    )


def load_bridge_occupation_education(
    conn: duckdb.DuckDBPyConnection,
    source_version: str,
    source_release_id: str,
    soc_version: str,
) -> None:
    """Load bridge_occupation_education from staging.

    Idempotent: skips if rows already exist for this source_version + source_release_id.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_occupation_education WHERE source_version = ? AND source_release_id = ?",
        [source_version, source_release_id],
    ).fetchone()[0]
    if existing > 0:
        return

    conn.execute(
        """INSERT INTO bridge_occupation_education
            (occupation_key, education_key, data_value, n, source_version, source_release_id)
            SELECT o.occupation_key, d.education_key, s.data_value, s.n, ?, ?
            FROM stage__onet__education s
            JOIN dim_occupation o ON o.soc_code = s.occupation_code AND o.soc_version = ?
            JOIN dim_education_requirement d
              ON d.element_id = s.element_id
              AND d.scale_id = s.scale_id
              AND d.category = s.category
              AND d.source_version = ?
            WHERE s.source_release_id = ?""",
        [source_version, source_release_id, soc_version, source_version, source_release_id],
    )


def load_onet_technology_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[OnetTechnologyRow],
    source_release_id: str,
) -> None:
    """Load parsed O*NET technology skills rows into staging.

    Idempotent: deletes existing rows for this release before inserting.
    """
    conn.execute("DELETE FROM stage__onet__technology_skills WHERE source_release_id = ?", [source_release_id])
    for r in rows:
        conn.execute(
            """INSERT INTO stage__onet__technology_skills
                (occupation_code, t2_type, example_name, commodity_code, commodity_title,
                 hot_technology, date, domain_source, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.occupation_code,
                r.t2_type,
                r.example_name,
                r.commodity_code,
                r.commodity_title,
                r.hot_technology,
                r.date,
                r.domain_source,
                r.source_release_id,
                r.parser_version,
            ],
        )


def load_dim_technology(
    conn: duckdb.DuckDBPyConnection,
    source_version: str,
) -> None:
    """Load dim_technology from staging.

    Inserts distinct (commodity_code, example_name) pairs not already present.
    """
    conn.execute(
        """INSERT INTO dim_technology
            (commodity_code, commodity_title, t2_type, example_name, source_version)
            SELECT DISTINCT s.commodity_code, s.commodity_title, s.t2_type, s.example_name, ?
            FROM stage__onet__technology_skills s
            WHERE NOT EXISTS (
                SELECT 1 FROM dim_technology d
                WHERE COALESCE(d.commodity_code, '') = COALESCE(s.commodity_code, '')
                  AND d.example_name = s.example_name
                  AND d.source_version = ?
            )""",
        [source_version, source_version],
    )


def load_bridge_occupation_technology(
    conn: duckdb.DuckDBPyConnection,
    source_version: str,
    source_release_id: str,
    soc_version: str,
) -> None:
    """Load bridge_occupation_technology from staging.

    Idempotent: skips if rows already exist for this source_version + source_release_id.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM bridge_occupation_technology WHERE source_version = ? AND source_release_id = ?",
        [source_version, source_release_id],
    ).fetchone()[0]
    if existing > 0:
        return

    conn.execute(
        """INSERT INTO bridge_occupation_technology
            (occupation_key, technology_key, hot_technology, source_version, source_release_id)
            SELECT o.occupation_key, d.technology_key, s.hot_technology, ?, ?
            FROM stage__onet__technology_skills s
            JOIN dim_occupation o ON o.soc_code = s.occupation_code AND o.soc_version = ?
            JOIN dim_technology d
              ON COALESCE(d.commodity_code, '') = COALESCE(s.commodity_code, '')
              AND d.example_name = s.example_name
              AND d.source_version = ?
            WHERE s.source_release_id = ?""",
        [source_version, source_release_id, soc_version, source_version, source_release_id],
    )
