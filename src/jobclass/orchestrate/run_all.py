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
        cpi_domain_refresh,
        cpi_refresh,
        crosswalk_refresh,
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
    print("\n[1/8] SOC Taxonomy Pipeline")
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

    # --- 1b. SOC Crosswalk (optional) ---
    if "soc_crosswalk" in by_name:
        print("\n[1b/8] SOC 2010↔2018 Crosswalk")
        summary.pipelines_attempted += 1
        try:
            xw_entry = by_name["soc_crosswalk"]
            xw_text, xw_version = _download_and_convert(xw_entry, raw_root)
            result = crosswalk_refresh(conn, xw_text, xw_version)
            if result.status == PipelineStatus.SUCCESS:
                print(f"  OK — Crosswalk loaded (run_id: {result.run_id})")
                summary.pipelines_succeeded += 1
            else:
                msg = f"  FAILED — {result.status.value}: {result.message}"
                print(msg)
                summary.pipelines_failed += 1
                summary.errors.append(msg)
        except Exception as e:
            msg = f"  ERROR — Crosswalk: {e}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)

    # --- 2. OEWS Employment & Wages (multi-vintage) ---
    # Find all OEWS national/state pairs and process each vintage
    oews_nat_entries = sorted(
        [e for e in entries if e.dataset_name.startswith("oews_national")],
        key=lambda e: e.dataset_name,
    )
    oews_st_entries = {
        e.dataset_name.replace("oews_state", ""): e for e in entries if e.dataset_name.startswith("oews_state")
    }
    oews_vintages = len(oews_nat_entries)
    oews_release = "unknown"
    for vi, nat_entry in enumerate(oews_nat_entries, 1):
        suffix = nat_entry.dataset_name.replace("oews_national", "")
        st_key = suffix
        st_entry = oews_st_entries.get(st_key)
        if not st_entry:
            msg = f"  SKIP — no matching oews_state{suffix} for {nat_entry.dataset_name}"
            print(msg)
            continue

        print(f"\n[2/8] OEWS Employment & Wages Pipeline (vintage {vi}/{oews_vintages}: {nat_entry.dataset_name})")
        summary.pipelines_attempted += 1
        try:
            nat_text, vintage_release = _download_and_convert(nat_entry, raw_root)
            st_text, _ = _download_and_convert(st_entry, raw_root)

            result = oews_refresh(conn, nat_text, st_text, vintage_release, soc_version)
            if result.status == PipelineStatus.SUCCESS:
                print(f"  OK — OEWS {vintage_release} loaded (run_id: {result.run_id})")
                summary.pipelines_succeeded += 1
                oews_release = vintage_release  # track last successful release
            else:
                msg = f"  FAILED — {result.status.value}: {result.message}"
                print(msg)
                summary.pipelines_failed += 1
                summary.errors.append(msg)
        except Exception as e:
            msg = f"  ERROR — OEWS {nat_entry.dataset_name}: {e}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)

    # --- 3. O*NET Semantic Descriptors ---
    print("\n[3/8] O*NET Semantic Descriptors Pipeline")
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

        # Optional new O*NET data sources
        wa_text = ed_text = tech_text = None
        if "onet_work_activities" in by_name:
            wa_text, _ = _download_and_convert(by_name["onet_work_activities"], raw_root)
        if "onet_education" in by_name:
            ed_text, _ = _download_and_convert(by_name["onet_education"], raw_root)
        if "onet_technology_skills" in by_name:
            tech_text, _ = _download_and_convert(by_name["onet_technology_skills"], raw_root)

        result = onet_refresh(
            conn,
            skills_text,
            knowledge_text,
            abilities_text,
            tasks_text,
            onet_version,
            onet_version,
            soc_version,
            work_activities_content=wa_text,
            education_content=ed_text,
            technology_content=tech_text,
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
    print("\n[4/8] Employment Projections Pipeline")
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

    # --- 5. CPI-U Price Index ---
    print("\n[5/8] CPI-U Price Index Pipeline")
    summary.pipelines_attempted += 1
    try:
        cpi_entry = by_name["bls_cpi"]
        cpi_raw, cpi_version = _download_entry(cpi_entry, raw_root)
        cpi_text = cpi_raw.decode("utf-8-sig")

        result = cpi_refresh(conn, cpi_text, cpi_version)
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — CPI loaded (run_id: {result.run_id})")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  FAILED — {result.status.value}: {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except Exception as e:
        msg = f"  ERROR — CPI: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)

    # --- 5b. CPI Domain Expansion ---
    print("\n[5b/8] CPI Domain Expansion Pipeline")
    summary.pipelines_attempted += 1
    try:
        cpi_item_entry = by_name["bls_cpi_item"]
        cpi_area_entry = by_name["bls_cpi_area"]
        cpi_series_entry = by_name["bls_cpi_series"]
        cpi_data_entry = by_name["bls_cpi_data_current"]

        cpi_item_raw, cpi_item_ver = _download_entry(cpi_item_entry, raw_root)
        cpi_area_raw, cpi_area_ver = _download_entry(cpi_area_entry, raw_root)
        cpi_series_raw, cpi_series_ver = _download_entry(cpi_series_entry, raw_root)
        cpi_data_raw, cpi_data_ver = _download_entry(cpi_data_entry, raw_root)

        result = cpi_domain_refresh(
            conn,
            item_content=cpi_item_raw.decode("utf-8-sig"),
            area_content=cpi_area_raw.decode("utf-8-sig"),
            series_content=cpi_series_raw.decode("utf-8-sig"),
            data_content=cpi_data_raw.decode("utf-8-sig"),
            source_release_id=cpi_item_ver,
        )
        if result.status == PipelineStatus.SUCCESS:
            print(f"  OK — CPI domain loaded (run_id: {result.run_id})")
            summary.pipelines_succeeded += 1
        else:
            msg = f"  FAILED — {result.status.value}: {result.message}"
            print(msg)
            summary.pipelines_failed += 1
            summary.errors.append(msg)
    except KeyError:
        print("  SKIP — CPI domain manifest entries not found (optional)")
    except Exception as e:
        msg = f"  ERROR — CPI Domain: {e}"
        print(msg)
        summary.pipelines_failed += 1
        summary.errors.append(msg)

    # --- 6. Warehouse Publish ---
    print("\n[6/8] Warehouse Publish (validation gate)")
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

    # --- 7. Time-Series Refresh ---
    print("\n[7/8] Time-Series Refresh")
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
