"""Manifest-driven extraction orchestrator.

Reads manifest entries and executes: download → checksum → store → register.
"""

from dataclasses import dataclass
from pathlib import Path

import duckdb

from jobclass.config.database import apply_migrations
from jobclass.extract.download import DownloadError, download_artifact
from jobclass.extract.manifest import ManifestEntry, load_enabled_entries
from jobclass.extract.storage import store_raw_artifact
from jobclass.extract.version_detect import detect_version
from jobclass.observe.logging import get_logger
from jobclass.observe.run_manifest import create_run_record, generate_run_id, update_run_counts

logger = get_logger(__name__)


@dataclass
class ExtractionResult:
    run_id: str
    dataset_name: str
    source_name: str
    raw_path: Path | None
    checksum: str | None
    source_release_id: str | None
    success: bool
    error: str | None = None


def extract_entry(
    entry: ManifestEntry,
    conn: duckdb.DuckDBPyConnection,
    raw_root: Path | None = None,
    run_id: str | None = None,
) -> ExtractionResult:
    """Execute the full extraction sequence for a single manifest entry."""
    rid = run_id or generate_run_id()

    try:
        # Download
        result = download_artifact(entry.dataset_url)

        # Detect version
        version = detect_version(
            entry.dataset_url,
            content=result.content[:4096].decode("utf-8", errors="replace"),
            strategy=entry.version_detection_rule or "url_pattern",
        )

        # Store immutably
        filename = entry.dataset_url.split("/")[-1]
        raw_path = store_raw_artifact(
            content=result.content,
            source_name=entry.source_name,
            dataset_name=entry.dataset_name,
            source_release_id=version or "unknown",
            run_id=rid,
            filename=filename,
            raw_root=raw_root,
        )

        # Register in run manifest
        create_run_record(
            conn,
            run_id=rid,
            pipeline_name=f"{entry.source_name}_refresh",
            dataset_name=entry.dataset_name,
            source_name=entry.source_name,
            source_url=entry.dataset_url,
            source_release_id=version,
            downloaded_at=result.downloaded_at,
            parser_name=entry.parser_name,
            parser_version="1.0.0",
            raw_checksum=result.checksum,
        )

        return ExtractionResult(
            run_id=rid,
            dataset_name=entry.dataset_name,
            source_name=entry.source_name,
            raw_path=raw_path,
            checksum=result.checksum,
            source_release_id=version,
            success=True,
        )

    except (DownloadError, Exception) as e:
        # Register failed run
        try:
            create_run_record(
                conn,
                run_id=rid,
                pipeline_name=f"{entry.source_name}_refresh",
                dataset_name=entry.dataset_name,
                source_name=entry.source_name,
                source_url=entry.dataset_url,
            )
            update_run_counts(conn, rid, load_status="failed", failure_classification="download_failure")
        except Exception as e:
            logger.warning("Failed to register failed run %s: %s", rid, e)

        return ExtractionResult(
            run_id=rid,
            dataset_name=entry.dataset_name,
            source_name=entry.source_name,
            raw_path=None,
            checksum=None,
            source_release_id=None,
            success=False,
            error=str(e),
        )


def extract_all(
    manifest_path: Path | str,
    conn: duckdb.DuckDBPyConnection,
    raw_root: Path | None = None,
) -> list[ExtractionResult]:
    """Extract all enabled manifest entries."""
    entries = load_enabled_entries(manifest_path)
    results = []
    for entry in entries:
        result = extract_entry(entry, conn, raw_root=raw_root)
        results.append(result)
    return results
