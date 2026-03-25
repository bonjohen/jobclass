"""SOC hierarchy and definitions parsers."""

import csv
import io
import re
from dataclasses import dataclass

PARSER_VERSION = "1.0.0"

# SOC level mapping — supports both XLSX format ("Major", "Minor", "Broad", "Detailed")
# and legacy CSV format ("Major Group", "Minor Group", "Broad Occupation", "Detailed Occupation")
LEVEL_MAP = {
    "Major Group": ("major_group", 1),
    "Minor Group": ("minor_group", 2),
    "Broad Occupation": ("broad_occupation", 3),
    "Detailed Occupation": ("detailed_occupation", 4),
    "Major": ("major_group", 1),
    "Minor": ("minor_group", 2),
    "Broad": ("broad_occupation", 3),
    "Detailed": ("detailed_occupation", 4),
}


@dataclass
class CrosswalkRow:
    source_soc_code: str
    source_soc_title: str
    source_soc_version: str
    target_soc_code: str
    target_soc_title: str
    target_soc_version: str
    mapping_type: str
    source_release_id: str
    parser_version: str = PARSER_VERSION


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


def _assign_parents(entries: list[tuple[str, int]]) -> dict[str, str | None]:
    """Data-driven parent assignment for SOC codes.

    Instead of mechanical derivation from code patterns, this builds the
    parent map by finding the nearest ancestor at the next higher level
    that actually exists in the data.

    Returns {soc_code: parent_soc_code_or_None}.
    """
    # Build sets of codes at each level
    codes_by_level: dict[int, set[str]] = {1: set(), 2: set(), 3: set(), 4: set()}
    for code, level in entries:
        codes_by_level[level].add(code)

    parents: dict[str, str | None] = {}

    for code, level in entries:
        if level == 1:
            parents[code] = None
            continue

        prefix, suffix = code.split("-")

        if level == 2:
            # Minor → Major is always XX-0000
            parents[code] = f"{prefix}-0000"
        elif level == 4:
            # Detailed → Broad: zero out last digit, with fallback.
            # SOC 2018 has some detailed codes whose mechanical broad parent
            # doesn't exist (e.g. 29-1221 → 29-1220 missing).
            mechanical = f"{prefix}-{suffix[:3]}0"
            if mechanical in codes_by_level[3]:
                parents[code] = mechanical
            else:
                # Find nearest existing broad in same prefix range
                best = None
                for broad in sorted(codes_by_level[3]):
                    if broad.startswith(prefix):
                        b_suffix = broad.split("-")[1]
                        if b_suffix <= suffix:
                            best = broad
                parents[code] = best or mechanical  # fallback to mechanical if nothing found
        elif level == 3:
            # Broad → Minor: find the actual minor group this code belongs to.
            # Try progressively coarser patterns until we find one that exists.
            candidates = [
                f"{prefix}-{suffix[:2]}00",  # try XX-YZ00 first
                f"{prefix}-{suffix[0]}000",  # then XX-Y000
            ]
            parent_code = None
            for c in candidates:
                if c in codes_by_level[2]:
                    parent_code = c
                    break
            # Last resort: find the closest minor group with matching prefix
            if parent_code is None:
                for minor in sorted(codes_by_level[2]):
                    if minor.startswith(prefix):
                        m_suffix = minor.split("-")[1]
                        if m_suffix <= suffix:
                            parent_code = minor
                # If still nothing, fall back to major
                if parent_code is None:
                    parent_code = f"{prefix}-0000"
            parents[code] = parent_code

    return parents


def parse_soc_hierarchy(content: str | bytes, source_release_id: str) -> list[SocHierarchyRow]:
    """Parse SOC hierarchy CSV file content into structured rows.

    Expected columns: SOC Group, SOC Code, SOC Title
    Uses data-driven parent assignment since SOC codes don't follow
    strict positional encoding patterns.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    # First pass: collect all entries with their levels
    entries: list[tuple[str, str, int, str]] = []  # (code, title, level_num, level_name)
    reader = csv.DictReader(io.StringIO(content))

    for raw in reader:
        group = raw.get("SOC Group", "").strip()
        code = raw.get("SOC Code", "").strip()
        title = raw.get("SOC Title", "").strip().strip('"')

        if not code or group not in LEVEL_MAP:
            continue

        level_name, level_num = LEVEL_MAP[group]
        entries.append((code, title, level_num, level_name))

    # Compute parents from actual data
    parent_map = _assign_parents([(code, level) for code, _, level, _ in entries])

    rows = []
    for code, title, level_num, level_name in entries:
        rows.append(
            SocHierarchyRow(
                soc_code=code,
                occupation_title=title,
                occupation_level=level_num,
                occupation_level_name=level_name,
                parent_soc_code=parent_map.get(code),
                source_release_id=source_release_id,
            )
        )

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

        rows.append(
            SocDefinitionRow(
                soc_code=code,
                occupation_definition=definition,
                source_release_id=source_release_id,
            )
        )

    return rows


def _classify_crosswalk_mappings(
    pairs: list[tuple[str, str, str, str]],
) -> dict[tuple[str, str], str]:
    """Classify each (source_code, target_code) pair by cardinality.

    Returns {(source_code, target_code): mapping_type}.
    """
    # Count how many targets each source maps to, and vice versa
    source_targets: dict[str, set[str]] = {}
    target_sources: dict[str, set[str]] = {}
    for src_code, _src_title, tgt_code, _tgt_title in pairs:
        source_targets.setdefault(src_code, set()).add(tgt_code)
        target_sources.setdefault(tgt_code, set()).add(src_code)

    result = {}
    for src_code, _src_title, tgt_code, _tgt_title in pairs:
        src_fan = len(source_targets[src_code])
        tgt_fan = len(target_sources[tgt_code])
        if src_fan == 1 and tgt_fan == 1:
            mapping_type = "1:1"
        elif src_fan > 1 and tgt_fan == 1:
            mapping_type = "split"
        elif src_fan == 1 and tgt_fan > 1:
            mapping_type = "merge"
        else:
            mapping_type = "complex"
        result[(src_code, tgt_code)] = mapping_type

    return result


def parse_soc_crosswalk(content: str | bytes, source_release_id: str) -> list[CrosswalkRow]:
    """Parse SOC 2010↔2018 crosswalk CSV content.

    Expected columns: 2010 SOC Code, 2010 SOC Title, 2018 SOC Code, 2018 SOC Title
    (column names are normalized from BLS XLSX format).
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    col_aliases = {
        "2010 soc code": "source_code",
        "2010 soc title": "source_title",
        "2018 soc code": "target_code",
        "2018 soc title": "target_title",
    }

    reader = csv.DictReader(io.StringIO(content))

    col_map: dict[str, str] = {}
    if reader.fieldnames:
        for raw_name in reader.fieldnames:
            normalized = raw_name.strip().lower()
            if normalized in col_aliases:
                col_map[raw_name] = col_aliases[normalized]

    # First pass: collect all pairs for classification
    raw_pairs: list[tuple[str, str, str, str]] = []
    for record in reader:
        src_code = ""
        src_title = ""
        tgt_code = ""
        tgt_title = ""
        for raw_col, alias in col_map.items():
            val = (record.get(raw_col) or "").strip().strip('"')
            if alias == "source_code":
                src_code = val
            elif alias == "source_title":
                src_title = val
            elif alias == "target_code":
                tgt_code = val
            elif alias == "target_title":
                tgt_title = val

        if not src_code or not tgt_code:
            continue
        if not re.match(r"\d{2}-\d{4}", src_code) or not re.match(r"\d{2}-\d{4}", tgt_code):
            continue
        raw_pairs.append((src_code, src_title, tgt_code, tgt_title))

    # Classify mappings
    classifications = _classify_crosswalk_mappings(raw_pairs)

    rows = []
    for src_code, src_title, tgt_code, tgt_title in raw_pairs:
        rows.append(
            CrosswalkRow(
                source_soc_code=src_code,
                source_soc_title=src_title,
                source_soc_version="2010",
                target_soc_code=tgt_code,
                target_soc_title=tgt_title,
                target_soc_version="2018",
                mapping_type=classifications[(src_code, tgt_code)],
                source_release_id=source_release_id,
            )
        )

    return rows
