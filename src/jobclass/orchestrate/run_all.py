"""End-to-end pipeline runner: download → convert → parse → load → publish.

Connects the extraction layer (manifest-driven downloads) to the pipeline
orchestrators (taxonomy_refresh, oews_refresh, etc.) via format conversion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from jobclass.extract.download import download_artifact
from jobclass.extract.formats import convert_to_text
from jobclass.extract.manifest import ManifestEntry, load_enabled_entries
from jobclass.extract.storage import store_raw_artifact
from jobclass.extract.version_detect import detect_version
from jobclass.observe.logging import get_logger
from jobclass.observe.run_manifest import generate_run_id

logger = get_logger(__name__)


@dataclass
class PipelineRunSummary:
    """Summary of a full pipeline run."""
    pipelines_attempted: int = 0
    pipelines_succeeded: int = 0
    pipelines_failed: int = 0
    errors: list[str] = field(default_factory=list)


def _download_entry(entry: ManifestEntry, raw_root: Path | None = None) -> tuple[bytes, str]:
    """Download a manifest entry and return (raw_bytes, detected_version)."""
    logger.info("  Downloading %s from %s", entry.dataset_name, entry.dataset_url)
    result = download_artifact(entry.dataset_url)
    version = detect_version(
        entry.dataset_url,
        content=result.content[:4096].decode("utf-8", errors="replace"),
        strategy=entry.version_detection_rule or "url_pattern",
    )
    version = version or "unknown"

    # Store immutably
    if raw_root:
        run_id = generate_run_id()
        filename = entry.dataset_url.split("/")[-1]
        store_raw_artifact(
            content=result.content,
            source_name=entry.source_name,
            dataset_name=entry.dataset_name,
            source_release_id=version,
            run_id=run_id,
            filename=filename,
            raw_root=raw_root,
        )

    return result.content, version


def _download_and_convert(entry: ManifestEntry, raw_root: Path | None = None) -> tuple[str, str]:
    """Download and convert to parser-ready text. Returns (text_content, version)."""
    raw_bytes, version = _download_entry(entry, raw_root)
    text = convert_to_text(raw_bytes, entry.expected_format, sheet_name=entry.sheet_name)
    return text, version


def run_all_pipelines(
    conn: duckdb.DuckDBPyConnection,
    manifest_path: Path | str,
    raw_root: Path | None = None,
) -> PipelineRunSummary:
    """Execute all pipelines end-to-end: download → convert → parse → load → publish."""
    from jobclass.orchestrate.pipelines import (
        PipelineStatus,
        oews_refresh,
        onet_refresh,
        projections_refresh,
        taxonomy_refresh,
        warehouse_publish,
    )

    summary = PipelineRunSummary()
    entries = load_enabled_entries(manifest_path)

    # Index entries by dataset_name for easy lookup
    by_name: dict[str, ManifestEntry] = {e.dataset_name: e for e in entries}

    # --- 1. SOC Taxonomy ---
    print("\n[1/5] SOC Taxonomy Pipeline")
    summary.pipelines_attempted += 1
    try:
        soc_h_entry = by_name["soc_hierarchy"]
        soc_d_entry = by_name["soc_definitions"]

        h_text, soc_version = _download_and_convert(soc_h_entry, raw_root)
        d_text, _ = _download_and_convert(soc_d_entry, raw_root)

        result = taxonomy_refresh(conn, h_text, d_text, soc_version, soc_version)
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — taxonomy loaded (run_id: {result.run_id})")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  FAILED — {result.status.value}: {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except Exception as e:
        msg = f"  ERROR — SOC: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)
        soc_version = "2018"  # fallback for downstream

    # --- 2. OEWS Employment & Wages ---
    print("\n[2/5] OEWS Employment & Wages Pipeline")
    summary.pipelines_attempted += 1
    try:
        nat_entry = by_name["oews_national"]
        st_entry = by_name["oews_state"]

        nat_text, oews_release = _download_and_convert(nat_entry, raw_root)
        st_text, _ = _download_and_convert(st_entry, raw_root)

        result = oews_refresh(conn, nat_text, st_text, oews_release, soc_version)
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — OEWS loaded (run_id: {result.run_id})")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  FAILED — {result.status.value}: {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except Exception as e:
        msg = f"  ERROR — OEWS: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)
        oews_release = "unknown"

    # --- 3. O*NET Semantic Descriptors ---
    print("\n[3/5] O*NET Semantic Descriptors Pipeline")
    summary.pipelines_attempted += 1
    try:
        skills_entry = by_name["onet_skills"]
        knowledge_entry = by_name["onet_knowledge"]
        abilities_entry = by_name["onet_abilities"]
        tasks_entry = by_name["onet_tasks"]

        skills_text, onet_version = _download_and_convert(skills_entry, raw_root)
        knowledge_text, _ = _download_and_convert(knowledge_entry, raw_root)
        abilities_text, _ = _download_and_convert(abilities_entry, raw_root)
        tasks_text, _ = _download_and_convert(tasks_entry, raw_root)

        result = onet_refresh(
            conn, skills_text, knowledge_text, abilities_text, tasks_text,
            onet_version, onet_version, soc_version,
        )
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — O*NET loaded (run_id: {result.run_id})")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  FAILED — {result.status.value}: {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except Exception as e:
        msg = f"  ERROR — O*NET: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)
        onet_version = "unknown"

    # --- 4. Employment Projections ---
    print("\n[4/5] Employment Projections Pipeline")
    summary.pipelines_attempted += 1
    try:
        proj_entry = by_name["bls_employment_projections"]

        proj_text, proj_release = _download_and_convert(proj_entry, raw_root)

        result = projections_refresh(conn, proj_text, proj_release, "2024-2034", soc_version)
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — Projections loaded (run_id: {result.run_id})")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  FAILED — {result.status.value}: {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except Exception as e:
        msg = f"  ERROR — Projections: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)

    # --- 5. Warehouse Publish ---
    print("\n[5/6] Warehouse Publish (validation gate)")
    summary.pipelines_attempted += 1
    try:
        result = warehouse_publish(conn, soc_version, oews_release, onet_version)
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — {result.message}")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  BLOCKED — {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except Exception as e:
        msg = f"  ERROR — Publish: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)

    # --- 6. Time-Series Refresh ---
    print("\n[6/6] Time-Series Refresh")
    summary.pipelines_attempted += 1
    try:
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh

        ts_results = timeseries_refresh(conn)
        failed_steps = [k for k, v in ts_results.items() if v < 0]
        if failed_steps:
            msg = f"  PARTIAL — {len(failed_steps)} step(s) failed: {', '.join(failed_steps)}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
        else:
            total_rows = sum(ts_results.values())
            print(f"  OK — time-series refresh complete ({total_rows:,} total rows)")
            summary.pipelines_succeeded += 1
    except Exception as e:
        msg = f"  ERROR — Time-Series: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)

    return summary
