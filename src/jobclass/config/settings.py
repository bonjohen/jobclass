"""Base configuration: environment handling, paths, constants."""

import os
from pathlib import Path

# Project root is four levels up from this file: src/jobclass/config/settings.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Overridable via environment variables
DB_PATH = Path(os.environ.get("JOBCLASS_DB_PATH", str(PROJECT_ROOT / "warehouse.duckdb")))
RAW_ROOT = Path(os.environ.get("JOBCLASS_RAW_ROOT", str(PROJECT_ROOT / "raw")))
MANIFEST_PATH = Path(os.environ.get("JOBCLASS_MANIFEST_PATH", str(PROJECT_ROOT / "config" / "source_manifest.yaml")))
MIGRATIONS_DIR = Path(os.environ.get("JOBCLASS_MIGRATIONS_DIR", str(PROJECT_ROOT / "migrations")))

# Constants (NFR-1: all timestamps UTC)
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
CHECKSUM_ALGORITHM = "sha256"

# Download retry settings
DOWNLOAD_MAX_RETRIES = 3
DOWNLOAD_BACKOFF_SECONDS = 2.0


def get_config() -> dict:
    """Return the full configuration as a dictionary."""
    return {
        "project_root": PROJECT_ROOT,
        "db_path": DB_PATH,
        "raw_root": RAW_ROOT,
        "manifest_path": MANIFEST_PATH,
        "migrations_dir": MIGRATIONS_DIR,
        "timestamp_format": TIMESTAMP_FORMAT,
        "checksum_algorithm": CHECKSUM_ALGORITHM,
        "download_max_retries": DOWNLOAD_MAX_RETRIES,
        "download_backoff_seconds": DOWNLOAD_BACKOFF_SECONDS,
    }
