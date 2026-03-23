"""Shared parsing utilities for all source file parsers."""

from __future__ import annotations

# Union of all suppression markers across BLS OEWS, O*NET, and BLS Projections.
SUPPRESSION_MARKERS = frozenset({"", "*", "**", "#", "-", "--", "N/A"})


def parse_float(value: str | None) -> float | None:
    """Parse a numeric string to float, returning None for empty/suppressed values.

    Handles BLS-style formatting: comma separators, percent signs, and all
    known suppression markers.
    """
    if value is None or value.strip() in SUPPRESSION_MARKERS:
        return None
    cleaned = value.strip().replace(",", "").replace("%", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def parse_int(value: str | None) -> int | None:
    """Parse a numeric string to int, returning None for empty/suppressed values.

    Uses float conversion internally to handle values like "1,234.0".
    """
    f = parse_float(value)
    return int(f) if f is not None else None
