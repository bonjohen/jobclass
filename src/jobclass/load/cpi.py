"""CPI-U price index loaders."""

from __future__ import annotations

import duckdb

from jobclass.parse.cpi import CPI_SERIES_ID, CpiRow


def load_cpi_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[CpiRow],
    source_release_id: str,
) -> None:
    """Load parsed CPI rows into staging.

    Idempotent: deletes existing rows for this release before inserting.
    """
    conn.execute("DELETE FROM stage__bls__cpi WHERE source_release_id = ?", [source_release_id])
    for r in rows:
        conn.execute(
            """INSERT INTO stage__bls__cpi
                (series_id, year, period, value, source_release_id, parser_version)
                VALUES (?, ?, ?, ?, ?, ?)""",
            [r.series_id, r.year, r.period, r.value, r.source_release_id, r.parser_version],
        )


def load_dim_price_index(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
) -> None:
    """Load dim_price_index — one row for CPI-U All Items.

    Idempotent: skips if series already exists.
    """
    existing = conn.execute(
        "SELECT COUNT(*) FROM dim_price_index WHERE series_id = ?",
        [CPI_SERIES_ID],
    ).fetchone()[0]
    if existing > 0:
        return
    conn.execute(
        """INSERT INTO dim_price_index
            (series_id, series_name, base_period, seasonally_adjusted, source_release_id)
            VALUES (?, ?, ?, ?, ?)""",
        [
            CPI_SERIES_ID,
            "CPI-U All Items, U.S. City Average, Seasonally Adjusted",
            "1982-84=100",
            True,
            source_release_id,
        ],
    )


def load_fact_price_index_observation(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
) -> None:
    """Load CPI observations from staging into the fact table.

    Joins to dim_time_period on year and dim_price_index on series_id.
    Idempotent: skips years already present.
    """
    conn.execute(
        """INSERT INTO fact_price_index_observation
            (price_index_key, period_key, index_value, source_release_id)
            SELECT pi.price_index_key, tp.period_key, s.value, ?
            FROM stage__bls__cpi s
            JOIN dim_price_index pi ON pi.series_id = s.series_id
            JOIN dim_time_period tp ON tp.year = s.year
            WHERE s.source_release_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM fact_price_index_observation f
                  WHERE f.price_index_key = pi.price_index_key
                    AND f.period_key = tp.period_key
              )""",
        [source_release_id, source_release_id],
    )
