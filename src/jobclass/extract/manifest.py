"""Source manifest reader — parses YAML manifest into structured entries."""

from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_FIELDS = {"source_name", "dataset_name", "dataset_url", "expected_format", "parser_name"}


@dataclass
class ManifestEntry:
    source_name: str
    dataset_name: str
    dataset_url: str
    expected_format: str
    parser_name: str
    refresh_cadence: str | None = None
    version_detection_rule: str | None = None
    enabled: bool = True


def load_manifest(manifest_path: Path | str) -> list[ManifestEntry]:
    """Load and validate source manifest, returning all entries."""
    path = Path(manifest_path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "sources" not in data:
        raise ValueError(f"Manifest at {path} missing 'sources' key")

    entries = []
    for i, raw in enumerate(data["sources"]):
        missing = REQUIRED_FIELDS - set(raw.keys())
        if missing:
            raise ValueError(f"Manifest entry {i} missing required fields: {missing}")
        entries.append(ManifestEntry(**{k: raw.get(k) for k in ManifestEntry.__dataclass_fields__}))

    return entries


def load_enabled_entries(manifest_path: Path | str) -> list[ManifestEntry]:
    """Load manifest and return only enabled entries."""
    return [e for e in load_manifest(manifest_path) if e.enabled]
