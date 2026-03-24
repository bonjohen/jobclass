"""OEWS staging and warehouse loaders."""

import duckdb

from jobclass.load import _safe_identifier
from jobclass.parse.oews import OewsRow

_STAGING_COLS = (
    "area_type, area_code, area_title, naics_code, naics_title, ownership_code, "
    "occupation_code, occupation_title, occupation_group, employment_count, "
    "employment_rse, jobs_per_1000, location_quotient, mean_hourly_wage, "
    "mean_annual_wage, mean_wage_rse, median_hourly_wage, median_annual_wage, "
    "p10_hourly_wage, p25_hourly_wage, p75_hourly_wage, p90_hourly_wage, "
    "p10_annual_wage, p25_annual_wage, p75_annual_wage, p90_annual_wage, "
    "source_release_id, parser_version"
)


def _row_to_tuple(row: OewsRow) -> tuple:
    return (
        row.area_type, row.area_code, row.area_title, row.naics_code,
        row.naics_title, row.ownership_code, row.occupation_code,
        row.occupation_title, row.occupation_group, row.employment_count,
        row.employment_rse, row.jobs_per_1000, row.location_quotient,
        row.mean_hourly_wage, row.mean_annual_wage, row.mean_wage_rse,
        row.median_hourly_wage, row.median_annual_wage,
        row.p10_hourly_wage, row.p25_hourly_wage, row.p75_hourly_wage,
        row.p90_hourly_wage, row.p10_annual_wage, row.p25_annual_wage,
        row.p75_annual_wage, row.p90_annual_wage,
        row.source_release_id, row.parser_version,
    )


def load_oews_staging(
    conn: duckdb.DuckDBPyConnection,
    rows: list[OewsRow],
    table_name: str,
    source_release_id: str,
) -> int:
    """Load parsed OEWS rows into a staging table. Idempotent per release."""
    table_name = _safe_identifier(table_name)
    conn.execute(f"DELETE FROM {table_name} WHERE source_release_id = ?", [source_release_id])
    placeholders = ", ".join(["?"] * 28)
    for row in rows:
        conn.execute(f"INSERT INTO {table_name} ({_STAGING_COLS}) VALUES ({placeholders})", list(_row_to_tuple(row)))
    return len(rows)


def load_dim_geography(
    conn: duckdb.DuckDBPyConnection,
    source_release_id: str,
) -> int:
    """Load dim_geography from OEWS staging. Appends new geo definitions only."""
    # Collect distinct geographies from both staging tables
    geo_rows = set()
    for table in ["stage__bls__oews_national", "stage__bls__oews_state"]:
        try:
            results = conn.execute(
                f"SELECT DISTINCT area_type, area_code, area_title FROM {table} WHERE source_release_id = ?",
                [source_release_id],
            ).fetchall()
            for r in results:
                geo_rows.add(r)
        except duckdb.CatalogException:
            pass

    loaded = 0
    for geo_type, geo_code, geo_name in geo_rows:
        exists = conn.execute(
            "SELECT COUNT(*) FROM dim_geography WHERE geo_type = ? AND geo_code = ? AND source_release_id = ?",
            [geo_type, geo_code, source_release_id],
        ).fetchone()[0]
        if exists > 0:
            continue

        state_fips = geo_code[:2] if geo_type == "state" and len(geo_code) >= 2 else None
        key = conn.execute("SELECT nextval('seq_geography_key')").fetchone()[0]
        conn.execute(
            """INSERT INTO dim_geography
            (geography_key, geo_type, geo_code, geo_name, state_fips, is_current, source_release_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [key, geo_type, geo_code, geo_name, state_fips, True, source_release_id],
        )
        loaded += 1
    return loaded


def load_dim_industry(
    conn: duckdb.DuckDBPyConnection,
    naics_version: str,
    source_release_id: str,
) -> int:
    """Load dim_industry from OEWS staging. Appends new NAICS codes only."""
    industry_rows = set()
    for table in ["stage__bls__oews_national", "stage__bls__oews_state"]:
        try:
            results = conn.execute(
                f"SELECT DISTINCT naics_code, naics_title FROM {table} WHERE source_release_id = ?",
                [source_release_id],
            ).fetchall()
            for r in results:
                if r[0]:
                    industry_rows.add(r)
        except duckdb.CatalogException:
            pass

    loaded = 0
    for naics_code, naics_title in industry_rows:
        exists = conn.execute(
            "SELECT COUNT(*) FROM dim_industry WHERE naics_code = ? AND naics_version = ?",
            [naics_code, naics_version],
        ).fetchone()[0]
        if exists > 0:
            continue

        key = conn.execute("SELECT nextval('seq_industry_key')").fetchone()[0]
        conn.execute(
            """INSERT INTO dim_industry
            (industry_key, naics_code, industry_title, naics_version, is_current)
            VALUES (?, ?, ?, ?, ?)""",
            [key, naics_code, naics_title, naics_version, True],
        )
        loaded += 1
    return loaded


def load_fact_occupation_employment_wages(
    conn: duckdb.DuckDBPyConnection,
    source_dataset: str,
    source_release_id: str,
    reference_period: str,
    soc_version: str,
) -> int:
    """Load fact table from OEWS staging. Idempotent per dataset+release."""
    # Check if already loaded
    existing = conn.execute(
        "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_dataset = ? AND source_release_id = ?",
        [source_dataset, source_release_id],
    ).fetchone()[0]
    if existing > 0:
        return 0

    _safe_identifier(source_dataset)
    table = f"stage__bls__{source_dataset}"
    try:
        estimate_year = int(reference_period.split(".")[0]) if "." in reference_period else int(reference_period[:4])
    except (ValueError, TypeError):
        estimate_year = 0

    staging_rows = conn.execute(
        f"SELECT * FROM {table} WHERE source_release_id = ?", [source_release_id]
    ).fetchall()
    cols = [d[0] for d in conn.description]

    loaded = 0
    for row in staging_rows:
        s = dict(zip(cols, row, strict=False))

        # Look up dimension keys
        occ_key = conn.execute(
            "SELECT occupation_key FROM dim_occupation WHERE soc_code = ? AND soc_version = ?",
            [s["occupation_code"], soc_version],
        ).fetchone()
        if not occ_key:
            continue
        occ_key = occ_key[0]

        geo_key = conn.execute(
            "SELECT geography_key FROM dim_geography WHERE geo_type = ? AND geo_code = ? AND source_release_id = ?",
            [s["area_type"], s["area_code"], source_release_id],
        ).fetchone()
        if not geo_key:
            continue
        geo_key = geo_key[0]

        ind_key = None
        if s.get("naics_code"):
            ind_row = conn.execute(
                "SELECT industry_key FROM dim_industry WHERE naics_code = ? LIMIT 1",
                [s["naics_code"]],
            ).fetchone()
            if ind_row:
                ind_key = ind_row[0]

        fact_id = conn.execute("SELECT nextval('seq_fact_oew_key')").fetchone()[0]
        conn.execute(
            """INSERT INTO fact_occupation_employment_wages
            (fact_id, reference_period, estimate_year, geography_key, industry_key,
             ownership_code, occupation_key, employment_count, employment_rse,
             jobs_per_1000, location_quotient, mean_hourly_wage, mean_annual_wage,
             median_hourly_wage, median_annual_wage, p10_hourly_wage, p25_hourly_wage,
             p75_hourly_wage, p90_hourly_wage, source_dataset, source_release_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [fact_id, reference_period, estimate_year, geo_key, ind_key,
             s["ownership_code"], occ_key, s["employment_count"], s["employment_rse"],
             s["jobs_per_1000"], s["location_quotient"], s["mean_hourly_wage"],
             s["mean_annual_wage"], s["median_hourly_wage"], s["median_annual_wage"],
             s["p10_hourly_wage"], s["p25_hourly_wage"], s["p75_hourly_wage"],
             s["p90_hourly_wage"], source_dataset, source_release_id],
        )
        loaded += 1

    return loaded
