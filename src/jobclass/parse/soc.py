"""SOC hierarchy and definitions parsers."""

import csv
import io
import re
from dataclasses import dataclass

PARSER_VERSION = "1.0.0"

# SOC level mapping
LEVEL_MAP = {
    "Major Group": ("major_group", 1),
    "Minor Group": ("minor_group", 2),
    "Broad Occupation": ("broad_occupation", 3),
    "Detailed Occupation": ("detailed_occupation", 4),
}


@dataclass
class SocHierarchyRow:
    soc_code: str
    occupation_title: str
    occupation_level: int
    occupation_level_name: str
    parent_soc_code: str | None
    source_release_id: str
    parser_version: str = PARSER_VERSION


@dataclass
class SocDefinitionRow:
    soc_code: str
    occupation_definition: str
    source_release_id: str
    parser_version: str = PARSER_VERSION


def _derive_parent_code(soc_code: str, level: int) -> str | None:
    """Derive parent SOC code from child code based on level rules.

    Major group (XX-0000) has no parent.
    Minor group (XX-YZ00) parent is major group (XX-0000).
    Broad occupation (XX-YZW0) parent is minor group (XX-YZ00).
    Detailed occupation (XX-YZWX) parent is broad occupation (XX-YZW0).
    """
    if level == 1:
        return None
    prefix, suffix = soc_code.split("-")
    if level == 2:
        return f"{prefix}-0000"
    elif level == 3:
        return f"{prefix}-{suffix[:2]}00"
    elif level == 4:
        return f"{prefix}-{suffix[:3]}0"
    return None


def parse_soc_hierarchy(content: str | bytes, source_release_id: str) -> list[SocHierarchyRow]:
    """Parse SOC hierarchy CSV file content into structured rows.

    Expected columns: SOC Group, SOC Code, SOC Title
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    rows = []
    reader = csv.DictReader(io.StringIO(content))

    for raw in reader:
        group = raw.get("SOC Group", "").strip()
        code = raw.get("SOC Code", "").strip()
        title = raw.get("SOC Title", "").strip().strip('"')

        if not code or group not in LEVEL_MAP:
            continue

        level_name, level_num = LEVEL_MAP[group]
        parent = _derive_parent_code(code, level_num)

        rows.append(SocHierarchyRow(
            soc_code=code,
            occupation_title=title,
            occupation_level=level_num,
            occupation_level_name=level_name,
            parent_soc_code=parent,
            source_release_id=source_release_id,
        ))

    return rows


def parse_soc_definitions(content: str | bytes, source_release_id: str) -> list[SocDefinitionRow]:
    """Parse SOC definitions CSV file content into structured rows.

    Expected columns: SOC Code, SOC Definition
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    rows = []
    reader = csv.DictReader(io.StringIO(content))

    for raw in reader:
        code = raw.get("SOC Code", "").strip()
        definition = raw.get("SOC Definition", "").strip().strip('"')

        if not code or not re.match(r"\d{2}-\d{4}", code):
            continue

        rows.append(SocDefinitionRow(
            soc_code=code,
            occupation_definition=definition,
            source_release_id=source_release_id,
        ))

    return rows
