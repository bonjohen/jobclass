"""OEWS national and state file parsers."""

import csv
import io
from dataclasses import dataclass

from jobclass.parse.common import parse_float, parse_int

PARSER_VERSION = "1.0.0"

# Area type mapping
AREA_TYPES = {"1": "national", "2": "state", "3": "msa", "4": "nonmetro"}

# BLS XLSX uses UPPERCASE column names and different names for some fields.
# This mapping normalizes XLSX column names to the parser's internal keys.
# Keys are lowercase source column names; values are the internal names the parser uses.
_OEWS_COLUMN_ALIASES = {
    "area": "area_code",       # XLSX uses AREA, not AREA_CODE
    "naics": "naics_code",     # XLSX uses NAICS, not NAICS_CODE
    "i_group": "i_group",      # industry group (not used by parser but present in XLSX)
    "prim_state": "prim_state",
    "pct_total": "pct_total",
    "pct_rpt": "pct_rpt",
    "annual": "annual",
    "hourly": "hourly",
}


def _normalize_oews_record(raw: dict) -> dict:
    """Normalize an OEWS CSV row: lowercase keys and apply column aliases.

    Handles both old-format CSV (lowercase keys like area_code) and new XLSX-
    derived CSV (UPPERCASE keys like AREA, NAICS).
    """
    normalized = {}
    for k, v in raw.items():
        key = k.strip().lower()
        # Apply alias mapping if it exists
        key = _OEWS_COLUMN_ALIASES.get(key, key)
        normalized[key] = v
    return normalized


@dataclass
class OewsRow:
    area_type: str
    area_code: str
    area_title: str
    naics_code: str
    naics_title: str
    ownership_code: str
    occupation_code: str
    occupation_title: str
    occupation_group: str
    employment_count: int | None
    employment_rse: float | None
    jobs_per_1000: float | None
    location_quotient: float | None
    mean_hourly_wage: float | None
    mean_annual_wage: float | None
    mean_wage_rse: float | None
    median_hourly_wage: float | None
    median_annual_wage: float | None
    p10_hourly_wage: float | None
    p25_hourly_wage: float | None
    p75_hourly_wage: float | None
    p90_hourly_wage: float | None
    p10_annual_wage: float | None
    p25_annual_wage: float | None
    p75_annual_wage: float | None
    p90_annual_wage: float | None
    source_release_id: str
    parser_version: str = PARSER_VERSION


def parse_oews(content: str | bytes, source_release_id: str) -> list[OewsRow]:
    """Parse OEWS CSV content (national or state) into standardized rows.

    Same parser handles both national and state formats since BLS uses
    identical column structure. Preserves suppressed values as None.

    Handles both lowercase column names (old CSV format) and UPPERCASE
    column names (XLSX-derived CSV from current BLS downloads).
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    rows = []
    reader = csv.DictReader(io.StringIO(content))

    for raw_record in reader:
        rec = _normalize_oews_record(raw_record)

        occ_code = rec.get("occ_code", "").strip()
        if not occ_code:
            continue

        rows.append(OewsRow(
            area_type=AREA_TYPES.get(rec.get("area_type", "").strip(), rec.get("area_type", "").strip()),
            area_code=rec.get("area_code", "").strip(),
            area_title=rec.get("area_title", "").strip(),
            naics_code=rec.get("naics_code", "").strip(),
            naics_title=rec.get("naics_title", "").strip(),
            ownership_code=rec.get("own_code", "").strip(),
            occupation_code=occ_code,
            occupation_title=rec.get("occ_title", "").strip().strip('"'),
            occupation_group=rec.get("o_group", "").strip(),
            employment_count=parse_int(rec.get("tot_emp")),
            employment_rse=parse_float(rec.get("emp_prse")),
            jobs_per_1000=parse_float(rec.get("jobs_1000")),
            location_quotient=parse_float(rec.get("loc_quotient")),
            mean_hourly_wage=parse_float(rec.get("h_mean")),
            mean_annual_wage=parse_float(rec.get("a_mean")),
            mean_wage_rse=parse_float(rec.get("mean_prse")),
            median_hourly_wage=parse_float(rec.get("h_median")),
            median_annual_wage=parse_float(rec.get("a_median")),
            p10_hourly_wage=parse_float(rec.get("h_pct10")),
            p25_hourly_wage=parse_float(rec.get("h_pct25")),
            p75_hourly_wage=parse_float(rec.get("h_pct75")),
            p90_hourly_wage=parse_float(rec.get("h_pct90")),
            p10_annual_wage=parse_float(rec.get("a_pct10")),
            p25_annual_wage=parse_float(rec.get("a_pct25")),
            p75_annual_wage=parse_float(rec.get("a_pct75")),
            p90_annual_wage=parse_float(rec.get("a_pct90")),
            source_release_id=source_release_id,
        ))

    return rows
