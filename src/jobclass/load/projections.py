"""Staging and warehouse loaders for Employment Projections."""

from __future__ import annotations

import duckdb

from jobclass.parse.projections import ProjectionRow


def load_projections_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[ProjectionRow],
    source_release_id: str,
) -> None:
    """Idempotent delete-and-reload for projections staging."""
    conn.execute(
        "DELETE FROM stage__bls__employment_projections WHERE source_release_id = ?",
        [source_release_id],
    )
    for r in rows:
        conn.execute(
            """INSERT INTO stage__bls__employment_projections (
                projection_cycle, occupation_code, occupation_title,
                base_year, projection_year,
                employment_base, employment_projected,
                employment_change_abs, employment_change_pct,
                annual_openings, education_category, training_category,
                work_experience_category, source_release_id, parser_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r.projection_cycle,
                r.occupation_code,
                r.occupation_title,
                r.base_year,
                r.projection_year,
                r.employment_base,
                r.employment_projected,
                r.employment_change_abs,
                r.employment_change_pct,
                r.annual_openings,
                r.education_category,
                r.training_category,
                r.work_experience_category,
                r.source_release_id,
                r.parser_version,
            ],
        )


def load_fact_occupation_projections(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
    soc_version: str,
) -> None:
    """Idempotent load: skip rows that already exist for this projection_cycle + occupation_key."""
    conn.execute(
        """INSERT INTO fact_occupation_projections (
            projection_cycle, occupation_key, base_year, projection_year,
            employment_base, employment_projected,
            employment_change_abs, employment_change_pct,
            annual_openings, education_category, training_category,
            work_experience_category, source_release_id
        )
        SELECT
            s.projection_cycle,
            o.occupation_key,
            s.base_year,
            s.projection_year,
            s.employment_base,
            s.employment_projected,
            s.employment_change_abs,
            s.employment_change_pct,
            s.annual_openings,
            s.education_category,
            s.training_category,
            s.work_experience_category,
            s.source_release_id
        FROM stage__bls__employment_projections s
        JOIN dim_occupation o
            ON s.occupation_code = o.soc_code AND o.soc_version = ?
        WHERE s.source_release_id = ?
          AND NOT EXISTS (
            SELECT 1 FROM fact_occupation_projections f
            WHERE f.projection_cycle = s.projection_cycle
              AND f.occupation_key = o.occupation_key
          )""",
        [soc_version, source_release_id],
    )
