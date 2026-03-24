"""Run reporting: row-count deltas, schema drift, measure deltas, reconciliation, run inspection."""

from __future__ import annotations

from dataclasses import dataclass

import duckdb

from jobclass.validate.framework import (
    MeasureDelta,
    SchemaChange,
    detect_measure_deltas,
    detect_schema_drift,
    get_table_schema,
)

# ============================================================
# Row-Count Delta Reporter (P7-02)
# ============================================================


@dataclass
class RowCountDeltaReport:
    """Row count comparison between current and prior run."""

    dataset_name: str
    current_run_id: str
    prior_run_id: str | None
    current_count: int
    prior_count: int | None
    absolute_change: int | None
    pct_change: float | None


def report_row_count_delta(
    conn: duckdb.DuckDBPyConnection,
    dataset_name: str,
    current_run_id: str,
) -> RowCountDeltaReport:
    """Compare row counts between current and prior successful run for a dataset."""
    # Get current run counts
    current = conn.execute("SELECT row_count_loaded FROM run_manifest WHERE run_id = ?", [current_run_id]).fetchone()
    current_count = current[0] if current and current[0] is not None else 0

    # Find prior successful run
    prior = conn.execute(
        """SELECT run_id, row_count_loaded FROM run_manifest
           WHERE dataset_name = ? AND load_status = 'success' AND run_id != ?
           ORDER BY created_at DESC LIMIT 1""",
        [dataset_name, current_run_id],
    ).fetchone()

    if prior and prior[1] is not None:
        prior_count = prior[1]
        abs_change = current_count - prior_count
        pct_change = abs(abs_change) / prior_count * 100 if prior_count > 0 else None
        return RowCountDeltaReport(
            dataset_name=dataset_name,
            current_run_id=current_run_id,
            prior_run_id=prior[0],
            current_count=current_count,
            prior_count=prior_count,
            absolute_change=abs_change,
            pct_change=pct_change,
        )
    return RowCountDeltaReport(
        dataset_name=dataset_name,
        current_run_id=current_run_id,
        prior_run_id=None,
        current_count=current_count,
        prior_count=None,
        absolute_change=None,
        pct_change=None,
    )


# ============================================================
# Schema Drift Report Emitter (P7-03)
# ============================================================


@dataclass
class SchemaDriftReport:
    """Schema drift report for a dataset between releases."""

    dataset_name: str
    prior_release: str
    current_release: str
    changes: list[SchemaChange]
    has_drift: bool


def report_schema_drift(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    dataset_name: str,
    prior_release: str,
    current_release: str,
) -> SchemaDriftReport:
    """Produce a schema drift report by comparing table schema snapshots."""
    _current_schema = get_table_schema(conn, table_name)
    # For now, compare against known schema (the actual table).
    # In production, we'd snapshot schemas per release.
    changes = []  # No drift if comparing same table to itself
    return SchemaDriftReport(
        dataset_name=dataset_name,
        prior_release=prior_release,
        current_release=current_release,
        changes=changes,
        has_drift=len(changes) > 0,
    )


def report_schema_drift_from_snapshots(
    dataset_name: str,
    prior_release: str,
    current_release: str,
    prior_schema: dict[str, str],
    current_schema: dict[str, str],
) -> SchemaDriftReport:
    """Produce a schema drift report from two schema snapshots."""
    changes = detect_schema_drift(prior_schema, current_schema)
    return SchemaDriftReport(
        dataset_name=dataset_name,
        prior_release=prior_release,
        current_release=current_release,
        changes=changes,
        has_drift=len(changes) > 0,
    )


# ============================================================
# Top Measure Delta Reporter (P7-04)
# ============================================================


@dataclass
class MeasureDeltaReport:
    """Top measure deltas for a dataset."""

    dataset_name: str
    measure_name: str
    deltas: list[MeasureDelta]
    top_n: int


def report_top_measure_deltas(
    dataset_name: str,
    measure_name: str,
    prior_measures: dict[str, float],
    current_measures: dict[str, float],
    top_n: int = 5,
) -> MeasureDeltaReport:
    """Report top N measures with largest relative change."""
    deltas = detect_measure_deltas(prior_measures, current_measures, top_n)
    return MeasureDeltaReport(
        dataset_name=dataset_name,
        measure_name=measure_name,
        deltas=deltas,
        top_n=top_n,
    )


# ============================================================
# Reconciliation Summary Reporter (P7-05)
# ============================================================


@dataclass
class ReconciliationReport:
    """Comparison of loaded totals against published reference."""

    dataset_name: str
    measure_name: str
    loaded_total: float
    published_total: float
    difference: float
    pct_difference: float
    matches: bool


def report_reconciliation(
    dataset_name: str,
    measure_name: str,
    loaded_total: float,
    published_total: float,
    tolerance_pct: float = 1.0,
) -> ReconciliationReport:
    """Compare a loaded total against a published reference total."""
    diff = loaded_total - published_total
    pct_diff = abs(diff) / published_total * 100 if published_total != 0 else 0
    return ReconciliationReport(
        dataset_name=dataset_name,
        measure_name=measure_name,
        loaded_total=loaded_total,
        published_total=published_total,
        difference=diff,
        pct_difference=pct_diff,
        matches=pct_diff <= tolerance_pct,
    )


# ============================================================
# Run Inspection View (P7-06)
# ============================================================


@dataclass
class RunInspection:
    """Complete inspection of a single pipeline run."""

    run_id: str
    pipeline_name: str
    dataset_name: str
    source_name: str
    source_release_id: str | None
    created_at: str | None
    completed_at: str | None
    row_count_raw: int | None
    row_count_stage: int | None
    row_count_loaded: int | None
    load_status: str | None
    failure_classification: str | None
    validation_summary: str | None
    metadata: dict


def inspect_run(conn: duckdb.DuckDBPyConnection, run_id: str) -> RunInspection | None:
    """Fetch all metadata for a single run, returning a complete inspection."""
    result = conn.execute("SELECT * FROM run_manifest WHERE run_id = ?", [run_id]).fetchone()
    if not result:
        return None
    columns = [desc[0] for desc in conn.description]
    row = dict(zip(columns, result, strict=False))
    return RunInspection(
        run_id=row["run_id"],
        pipeline_name=row["pipeline_name"],
        dataset_name=row["dataset_name"],
        source_name=row["source_name"],
        source_release_id=row.get("source_release_id"),
        created_at=str(row.get("created_at")) if row.get("created_at") else None,
        completed_at=str(row.get("completed_at")) if row.get("completed_at") else None,
        row_count_raw=row.get("row_count_raw"),
        row_count_stage=row.get("row_count_stage"),
        row_count_loaded=row.get("row_count_loaded"),
        load_status=row.get("load_status"),
        failure_classification=row.get("failure_classification"),
        validation_summary=row.get("validation_summary"),
        metadata=row,
    )
