"""Parser for BLS Employment Projections data."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

PARSER_VERSION = "1.0.0"


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


def _safe_int(value: str | None) -> int | None:
    """Parse integer, returning None for empty/suppressed values."""
    if not value or value.strip() in ("", "--", "N/A", "#", "**", "*"):
        return None
    cleaned = value.strip().replace(",", "")
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _safe_float(value: str | None) -> float | None:
    """Parse float, returning None for empty/suppressed values."""
    if not value or value.strip() in ("", "--", "N/A", "#", "**", "*"):
        return None
    cleaned = value.strip().replace(",", "").replace("%", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def parse_employment_projections(
    content: str,
    source_release_id: str,
    projection_cycle: str | None = None,
) -> list[ProjectionRow]:
    """Parse BLS Employment Projections TSV/CSV content.

    The projection_cycle (e.g. "2022-2032") can be provided explicitly
    or derived from base_year and projection_year columns.
    """
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")

    rows: list[ProjectionRow] = []
    for record in reader:
        # Normalize field names to lower/snake
        rec = {k.strip().lower().replace(" ", "_").replace("-", "_"): v
               for k, v in record.items()}

        occ_code = rec.get("occupation_code", rec.get("soc_code", "")).strip()
        occ_title = rec.get("occupation_title", rec.get("title", "")).strip()

        base_year = _safe_int(rec.get("base_year", rec.get("employment_base_year", "")))
        proj_year = _safe_int(rec.get("projection_year", rec.get("employment_projection_year", "")))

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
            employment_base=_safe_int(rec.get("employment_base", rec.get("employment_2022", ""))),
            employment_projected=_safe_int(rec.get("employment_projected", rec.get("employment_2032", ""))),
            employment_change_abs=_safe_int(rec.get("employment_change_abs", rec.get("employment_change", ""))),
            employment_change_pct=_safe_float(rec.get("employment_change_pct", rec.get("employment_change_percent", ""))),
            annual_openings=_safe_int(rec.get("annual_openings", rec.get("occupational_openings", ""))),
            education_category=rec.get("education_category", rec.get("typical_entry_level_education", None)),
            training_category=rec.get("training_category", rec.get("on_the_job_training", None)),
            work_experience_category=rec.get("work_experience_category", rec.get("work_experience", None)),
            source_release_id=source_release_id,
            parser_version=PARSER_VERSION,
        ))

    return rows
