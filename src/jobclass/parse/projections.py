"""Parser for BLS Employment Projections data.

Handles two input formats:
1. XLSX-derived CSV from BLS ind-occ-matrix/occupation.xlsx (current BLS format):
   Column names like "2024 National Employment Matrix code", "Employment, 2024", etc.
   Employment values are in THOUSANDS (e.g. 309.4 means 309,400).
2. Legacy TSV format (used in older tests):
   Column names like occupation_code, employment_base, etc.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

from jobclass.parse.common import parse_float, parse_int

PARSER_VERSION = "1.1.0"


@dataclass
class ProjectionRow:
    """Parsed projection row."""
    projection_cycle: str
    occupation_code: str
    occupation_title: str
    base_year: int
    projection_year: int
    employment_base: int | None
    employment_projected: int | None
    employment_change_abs: int | None
    employment_change_pct: float | None
    annual_openings: int | None
    education_category: str | None
    training_category: str | None
    work_experience_category: str | None
    source_release_id: str
    parser_version: str


def _find_column(headers: list[str], *patterns: str) -> str | None:
    """Find a column name containing all given patterns (case-insensitive)."""
    for h in headers:
        h_lower = h.lower()
        if all(p.lower() in h_lower for p in patterns):
            return h
    return None


def _thousands_to_int(value: str | None) -> int | None:
    """Parse a value expressed in thousands to an integer count.

    BLS projections express employment in thousands (e.g. 309.4 = 309,400).
    """
    f = parse_float(value)
    if f is None:
        return None
    return int(round(f * 1000))


def _detect_years_from_headers(headers: list[str]) -> tuple[int | None, int | None]:
    """Extract base and projection years from BLS column names.

    Looks for patterns like "Employment, 2024" and "Employment, 2034".
    """
    emp_years = []
    for h in headers:
        h_lower = h.lower()
        # Match "employment, YYYY" but not "employment change" or "employment distribution"
        if h_lower.startswith("employment") and "change" not in h_lower and "distribution" not in h_lower:
            m = re.search(r"(\d{4})", h)
            if m:
                emp_years.append(int(m.group(1)))
    emp_years = sorted(set(emp_years))
    if len(emp_years) >= 2:
        return emp_years[0], emp_years[-1]
    return None, None


def _is_bls_xlsx_format(headers: list[str]) -> bool:
    """Detect if the CSV was produced from a BLS XLSX projections file."""
    return any("matrix" in h.lower() for h in headers)


def _parse_bls_xlsx_format(
    reader: csv.DictReader,
    headers: list[str],
    source_release_id: str,
    projection_cycle: str | None,
) -> list[ProjectionRow]:
    """Parse BLS XLSX-derived CSV with long descriptive column names."""
    col_code = _find_column(headers, "matrix", "code")
    col_title = _find_column(headers, "matrix", "title")
    col_type = _find_column(headers, "occupation", "type")

    # Find employment base/projected columns (e.g. "Employment, 2024", "Employment, 2034")
    emp_cols = []
    for h in headers:
        h_lower = h.lower()
        if h_lower.startswith("employment") and "change" not in h_lower and "distribution" not in h_lower:
            if re.search(r"\d{4}", h):
                emp_cols.append(h)
    col_emp_base = emp_cols[0] if len(emp_cols) >= 1 else None
    col_emp_proj = emp_cols[1] if len(emp_cols) >= 2 else None

    col_change_abs = _find_column(headers, "employment change", "numeric")
    col_change_pct = _find_column(headers, "employment change", "percent")
    col_openings = _find_column(headers, "openings")
    col_wage = _find_column(headers, "median", "wage")
    col_education = _find_column(headers, "education")
    col_training = _find_column(headers, "training")
    col_experience = _find_column(headers, "work experience")

    base_year, proj_year = _detect_years_from_headers(headers)
    cycle = projection_cycle
    if not cycle and base_year and proj_year:
        cycle = f"{base_year}-{proj_year}"
    cycle = cycle or source_release_id

    rows: list[ProjectionRow] = []
    for record in reader:
        occ_code = (record.get(col_code, "") or "").strip() if col_code else ""
        occ_title = (record.get(col_title, "") or "").strip() if col_title else ""

        # Skip empty rows, non-SOC codes, and summary/aggregate rows
        if not occ_code or not re.match(r"\d{2}-\d{4}", occ_code):
            continue
        occ_type = (record.get(col_type, "") or "").strip() if col_type else ""
        if occ_type.lower() == "summary":
            continue

        # Employment values are in thousands — convert to actual counts
        emp_base = _thousands_to_int(record.get(col_emp_base)) if col_emp_base else None
        emp_proj = _thousands_to_int(record.get(col_emp_proj)) if col_emp_proj else None
        change_abs = _thousands_to_int(record.get(col_change_abs)) if col_change_abs else None
        change_pct = parse_float(record.get(col_change_pct)) if col_change_pct else None
        openings = _thousands_to_int(record.get(col_openings)) if col_openings else None

        rows.append(ProjectionRow(
            projection_cycle=cycle,
            occupation_code=occ_code,
            occupation_title=occ_title,
            base_year=base_year or 0,
            projection_year=proj_year or 0,
            employment_base=emp_base,
            employment_projected=emp_proj,
            employment_change_abs=change_abs,
            employment_change_pct=change_pct,
            annual_openings=openings,
            education_category=(record.get(col_education, "") or "").strip() or None if col_education else None,
            training_category=(record.get(col_training, "") or "").strip() or None if col_training else None,
            work_experience_category=(record.get(col_experience, "") or "").strip() or None if col_experience else None,
            source_release_id=source_release_id,
            parser_version=PARSER_VERSION,
        ))

    return rows


def _parse_legacy_format(
    reader: csv.DictReader,
    source_release_id: str,
    projection_cycle: str | None,
) -> list[ProjectionRow]:
    """Parse legacy TSV/CSV format with simple column names."""
    rows: list[ProjectionRow] = []
    for record in reader:
        # Normalize field names to lower/snake
        rec = {k.strip().lower().replace(" ", "_").replace("-", "_"): v
               for k, v in record.items()}

        occ_code = rec.get("occupation_code", rec.get("soc_code", "")).strip()
        occ_title = rec.get("occupation_title", rec.get("title", "")).strip()

        base_year = parse_int(rec.get("base_year", rec.get("employment_base_year", "")))
        proj_year = parse_int(rec.get("projection_year", rec.get("employment_projection_year", "")))

        cycle = projection_cycle
        if not cycle and base_year and proj_year:
            cycle = f"{base_year}-{proj_year}"
        cycle = cycle or source_release_id

        rows.append(ProjectionRow(
            projection_cycle=cycle,
            occupation_code=occ_code,
            occupation_title=occ_title,
            base_year=base_year or 0,
            projection_year=proj_year or 0,
            employment_base=parse_int(rec.get("employment_base", rec.get("employment_2022", ""))),
            employment_projected=parse_int(rec.get("employment_projected", rec.get("employment_2032", ""))),
            employment_change_abs=parse_int(rec.get("employment_change_abs", rec.get("employment_change", ""))),
            employment_change_pct=parse_float(rec.get("employment_change_pct", rec.get("employment_change_percent", ""))),
            annual_openings=parse_int(rec.get("annual_openings", rec.get("occupational_openings", ""))),
            education_category=rec.get("education_category", rec.get("typical_entry_level_education", None)),
            training_category=rec.get("training_category", rec.get("on_the_job_training", None)),
            work_experience_category=rec.get("work_experience_category", rec.get("work_experience", None)),
            source_release_id=source_release_id,
            parser_version=PARSER_VERSION,
        ))

    return rows


def parse_employment_projections(
    content: str,
    source_release_id: str,
    projection_cycle: str | None = None,
) -> list[ProjectionRow]:
    """Parse BLS Employment Projections content.

    Auto-detects format: BLS XLSX-derived CSV (with "Matrix" column names and
    employment in thousands) vs legacy TSV (with simple column names).
    """
    # Sniff delimiter: if tabs are present in header line, use TSV
    first_line = content.split("\n", 1)[0]
    delimiter = "\t" if "\t" in first_line else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    headers = reader.fieldnames or []

    if _is_bls_xlsx_format(headers):
        return _parse_bls_xlsx_format(reader, headers, source_release_id, projection_cycle)
    else:
        return _parse_legacy_format(reader, source_release_id, projection_cycle)
