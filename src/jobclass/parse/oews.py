"""OEWS national and state file parsers."""

import csv
import io
from dataclasses import dataclass

PARSER_VERSION = "1.0.0"

# BLS suppression markers that should become None
SUPPRESSION_MARKERS = {"**", "#", "N/A", "*", "-", ""}

# Area type mapping
AREA_TYPES = {"1": "national", "2": "state", "3": "msa", "4": "nonmetro"}


def _parse_numeric(value: str | None) -> float | None:
    """Parse a numeric value, preserving BLS suppressions as None."""
    if value is None or value.strip() in SUPPRESSION_MARKERS:
        return None
    try:
        return float(value.strip().replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_int(value: str | None) -> int | None:
    """Parse an integer value, preserving BLS suppressions as None."""
    f = _parse_numeric(value)
    return int(f) if f is not None else None


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
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    rows = []
    reader = csv.DictReader(io.StringIO(content))

    for raw in reader:
        occ_code = raw.get("occ_code", "").strip()
        if not occ_code:
            continue

        rows.append(OewsRow(
            area_type=AREA_TYPES.get(raw.get("area_type", "").strip(), raw.get("area_type", "").strip()),
            area_code=raw.get("area_code", "").strip(),
            area_title=raw.get("area_title", "").strip(),
            naics_code=raw.get("naics_code", "").strip(),
            naics_title=raw.get("naics_title", "").strip(),
            ownership_code=raw.get("own_code", "").strip(),
            occupation_code=occ_code,
            occupation_title=raw.get("occ_title", "").strip().strip('"'),
            occupation_group=raw.get("o_group", "").strip(),
            employment_count=_parse_int(raw.get("tot_emp")),
            employment_rse=_parse_numeric(raw.get("emp_prse")),
            jobs_per_1000=_parse_numeric(raw.get("jobs_1000")),
            location_quotient=_parse_numeric(raw.get("loc_quotient")),
            mean_hourly_wage=_parse_numeric(raw.get("h_mean")),
            mean_annual_wage=_parse_numeric(raw.get("a_mean")),
            mean_wage_rse=_parse_numeric(raw.get("mean_prse")),
            median_hourly_wage=_parse_numeric(raw.get("h_median")),
            median_annual_wage=_parse_numeric(raw.get("a_median")),
            p10_hourly_wage=_parse_numeric(raw.get("h_pct10")),
            p25_hourly_wage=_parse_numeric(raw.get("h_pct25")),
            p75_hourly_wage=_parse_numeric(raw.get("h_pct75")),
            p90_hourly_wage=_parse_numeric(raw.get("h_pct90")),
            p10_annual_wage=_parse_numeric(raw.get("a_pct10")),
            p25_annual_wage=_parse_numeric(raw.get("a_pct25")),
            p75_annual_wage=_parse_numeric(raw.get("a_pct75")),
            p90_annual_wage=_parse_numeric(raw.get("a_pct90")),
            source_release_id=source_release_id,
        ))

    return rows
