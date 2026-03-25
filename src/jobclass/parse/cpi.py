"""BLS CPI-U (Consumer Price Index for All Urban Consumers) parser.

Parses the BLS time series flat file format (whitespace-padded columns).
Filters to series CUSR0000SA0 (All Items, U.S. city average, seasonally adjusted)
and period M13 (annual average).
"""

from __future__ import annotations

from dataclasses import dataclass

PARSER_VERSION = "1.0.0"

# CPI-U All Items, Seasonally Adjusted, U.S. City Average
CPI_SERIES_ID = "CUSR0000SA0"


@dataclass
class CpiRow:
    """Parsed CPI observation."""

    series_id: str
    year: int
    period: str
    value: float
    source_release_id: str
    parser_version: str


def parse_cpi(content: str, source_release_id: str) -> list[CpiRow]:
    """Parse BLS CPI flat file content.

    The BLS time series flat files have whitespace-padded columns:
    series_id (17 chars), year (5 chars), period (4 chars), value, footnotes.

    Filters to:
    - Series CUSR0000SA0 (CPI-U All Items, seasonally adjusted)
    - Period M13 (annual average)
    """
    rows = []
    for line in content.splitlines():
        line = line.rstrip()
        if not line or line.startswith("series_id"):
            continue
        # BLS format: tab-separated with possible extra whitespace
        parts = line.split()
        if len(parts) < 4:
            continue
        series_id = parts[0].strip()
        if series_id != CPI_SERIES_ID:
            continue
        period = parts[2].strip()
        if period != "M13":
            continue
        try:
            year = int(parts[1].strip())
            value = float(parts[3].strip())
        except (ValueError, IndexError):
            continue
        rows.append(
            CpiRow(
                series_id=series_id,
                year=year,
                period=period,
                value=value,
                source_release_id=source_release_id,
                parser_version=PARSER_VERSION,
            )
        )
    return rows
