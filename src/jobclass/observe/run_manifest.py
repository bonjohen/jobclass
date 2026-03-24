"""Run manifest operations — create, update, and query pipeline run records."""

import uuid
from datetime import UTC, datetime

import duckdb


def generate_run_id() -> str:
    """Generate a unique run ID."""
    return str(uuid.uuid4())


def create_run_record(
    conn: duckdb.DuckDBPyConnection,
    *,
    run_id: str,
    pipeline_name: str,
    dataset_name: str,
    source_name: str,
    source_url: str | None = None,
    source_release_id: str | None = None,
    downloaded_at: str | None = None,
    parser_name: str | None = None,
    parser_version: str | None = None,
    raw_checksum: str | None = None,
) -> str:
    """Insert a new run manifest record. Returns the run_id."""
    conn.execute(
        """
        INSERT INTO run_manifest (
            run_id, pipeline_name, dataset_name, source_name,
            source_url, source_release_id, downloaded_at,
            parser_name, parser_version, raw_checksum, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            run_id,
            pipeline_name,
            dataset_name,
            source_name,
            source_url,
            source_release_id,
            downloaded_at,
            parser_name,
            parser_version,
            raw_checksum,
            datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ],
    )
    return run_id


def update_run_counts(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    *,
    row_count_raw: int | None = None,
    row_count_stage: int | None = None,
    row_count_loaded: int | None = None,
    load_status: str | None = None,
    failure_classification: str | None = None,
    validation_summary: str | None = None,
) -> None:
    """Update run manifest with row counts and completion status."""
    conn.execute(
        """
        UPDATE run_manifest SET
            row_count_raw = COALESCE(?, row_count_raw),
            row_count_stage = COALESCE(?, row_count_stage),
            row_count_loaded = COALESCE(?, row_count_loaded),
            load_status = COALESCE(?, load_status),
            failure_classification = COALESCE(?, failure_classification),
            validation_summary = COALESCE(?, validation_summary),
            completed_at = ?
        WHERE run_id = ?
        """,
        [
            row_count_raw,
            row_count_stage,
            row_count_loaded,
            load_status,
            failure_classification,
            validation_summary,
            datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            run_id,
        ],
    )


def get_run(conn: duckdb.DuckDBPyConnection, run_id: str) -> dict | None:
    """Fetch a single run manifest record as a dict."""
    result = conn.execute("SELECT * FROM run_manifest WHERE run_id = ?", [run_id]).fetchone()
    if not result:
        return None
    columns = [desc[0] for desc in conn.description]
    return dict(zip(columns, result, strict=False))
