"""Pipeline orchestration: taxonomy_refresh, oews_refresh, onet_refresh, warehouse_publish."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import duckdb

from jobclass.observe.run_manifest import (
    create_run_record, generate_run_id, update_run_counts,
)
from jobclass.validate.framework import (
    FailureClassification,
    ValidationResult,
    check_publication_gate,
    validate_grain_uniqueness,
    validate_referential_integrity,
    validate_required_columns,
)


class PipelineStatus(str, Enum):
    SUCCESS = "success"
    VALIDATION_FAILURE = "validation_failure"
    LOAD_FAILURE = "load_failure"
    DEPENDENCY_BLOCKED = "dependency_blocked"
    PUBLISH_BLOCKED = "publish_blocked"


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    pipeline_name: str
    status: PipelineStatus
    run_id: str | None = None
    message: str = ""
    validation_results: list[ValidationResult] = field(default_factory=list)


# ============================================================
# Dependency checking
# ============================================================

def check_taxonomy_loaded(conn: duckdb.DuckDBPyConnection, soc_version: str) -> bool:
    """Check if taxonomy (dim_occupation) is loaded for the given SOC version."""
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM dim_occupation WHERE soc_version = ?", [soc_version]
        ).fetchone()[0]
        return count > 0
    except Exception:
        return False


# ============================================================
# taxonomy_refresh (P8-01)
# ============================================================

def taxonomy_refresh(
    conn: duckdb.DuckDBPyConnection,
    hierarchy_content: str,
    definitions_content: str,
    soc_version: str,
    source_release_id: str,
) -> PipelineResult:
    """Execute the full SOC taxonomy pipeline: parse → validate → load."""
    from jobclass.parse.soc import parse_soc_hierarchy, parse_soc_definitions
    from jobclass.load.soc import (
        load_soc_hierarchy_staging, load_soc_definitions_staging,
        load_dim_occupation, load_bridge_occupation_hierarchy,
    )
    from jobclass.validate.soc import validate_soc_structural, validate_soc_hierarchy_completeness

    run_id = generate_run_id()
    create_run_record(
        conn, run_id=run_id, pipeline_name="taxonomy_refresh",
        dataset_name="soc", source_name="soc",
        source_release_id=source_release_id,
    )

    try:
        # Parse
        hierarchy = parse_soc_hierarchy(hierarchy_content, soc_version)
        definitions = parse_soc_definitions(definitions_content, soc_version)

        # Load staging
        load_soc_hierarchy_staging(conn, hierarchy, soc_version)
        load_soc_definitions_staging(conn, definitions, soc_version)

        # Validate
        validations = validate_soc_structural(conn, source_release_id=soc_version)
        completeness = validate_soc_hierarchy_completeness(conn, soc_version)
        validations.append(completeness)

        failures = [v for v in validations if not v.passed]
        if failures:
            update_run_counts(
                conn, run_id, load_status="validation_failure",
                failure_classification=FailureClassification.VALIDATION_FAILURE.value,
                validation_summary=f"{len(failures)} checks failed",
            )
            return PipelineResult(
                pipeline_name="taxonomy_refresh",
                status=PipelineStatus.VALIDATION_FAILURE,
                run_id=run_id,
                message=f"{len(failures)} validation(s) failed",
                validation_results=validations,
            )

        # Load warehouse
        load_dim_occupation(conn, soc_version, soc_version)
        load_bridge_occupation_hierarchy(conn, soc_version, soc_version)

        stage_count = conn.execute(
            "SELECT COUNT(*) FROM stage__soc__hierarchy WHERE source_release_id = ?", [soc_version]
        ).fetchone()[0]
        dim_count = conn.execute(
            "SELECT COUNT(*) FROM dim_occupation WHERE soc_version = ?", [soc_version]
        ).fetchone()[0]

        update_run_counts(
            conn, run_id,
            row_count_raw=len(hierarchy) + len(definitions),
            row_count_stage=stage_count,
            row_count_loaded=dim_count,
            load_status="success",
            validation_summary=f"{len(validations)} checks passed",
        )
        return PipelineResult(
            pipeline_name="taxonomy_refresh",
            status=PipelineStatus.SUCCESS,
            run_id=run_id,
            validation_results=validations,
        )
    except Exception as e:
        update_run_counts(
            conn, run_id, load_status="load_failure",
            failure_classification=FailureClassification.LOAD_FAILURE.value,
        )
        return PipelineResult(
            pipeline_name="taxonomy_refresh",
            status=PipelineStatus.LOAD_FAILURE,
            run_id=run_id,
            message=str(e),
        )


# ============================================================
# oews_refresh (P8-02)
# ============================================================

def oews_refresh(
    conn: duckdb.DuckDBPyConnection,
    national_content: str,
    state_content: str,
    release_id: str,
    soc_version: str,
) -> PipelineResult:
    """Execute the OEWS pipeline: parse → validate → load."""
    from jobclass.parse.oews import parse_oews
    from jobclass.load.oews import (
        load_oews_staging, load_dim_geography, load_dim_industry,
        load_fact_occupation_employment_wages,
    )

    # Check dependency
    if not check_taxonomy_loaded(conn, soc_version):
        return PipelineResult(
            pipeline_name="oews_refresh",
            status=PipelineStatus.DEPENDENCY_BLOCKED,
            message=f"dim_occupation not loaded for SOC version {soc_version}",
        )

    run_id = generate_run_id()
    create_run_record(
        conn, run_id=run_id, pipeline_name="oews_refresh",
        dataset_name="oews", source_name="bls",
        source_release_id=release_id,
    )

    try:
        nat = parse_oews(national_content, release_id)
        st = parse_oews(state_content, release_id)

        load_oews_staging(conn, nat, "stage__bls__oews_national", release_id)
        load_oews_staging(conn, st, "stage__bls__oews_state", release_id)
        load_dim_geography(conn, release_id)
        load_dim_industry(conn, "2022", release_id)
        load_fact_occupation_employment_wages(conn, "oews_national", release_id, release_id, soc_version)
        load_fact_occupation_employment_wages(conn, "oews_state", release_id, release_id, soc_version)

        fact_count = conn.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE source_release_id = ?", [release_id]
        ).fetchone()[0]

        update_run_counts(
            conn, run_id,
            row_count_raw=len(nat) + len(st),
            row_count_stage=len(nat) + len(st),
            row_count_loaded=fact_count,
            load_status="success",
        )
        return PipelineResult(
            pipeline_name="oews_refresh", status=PipelineStatus.SUCCESS, run_id=run_id,
        )
    except Exception as e:
        update_run_counts(
            conn, run_id, load_status="load_failure",
            failure_classification=FailureClassification.LOAD_FAILURE.value,
        )
        return PipelineResult(
            pipeline_name="oews_refresh", status=PipelineStatus.LOAD_FAILURE,
            run_id=run_id, message=str(e),
        )


# ============================================================
# onet_refresh (P8-03)
# ============================================================

def onet_refresh(
    conn: duckdb.DuckDBPyConnection,
    skills_content: str,
    knowledge_content: str,
    abilities_content: str,
    tasks_content: str,
    onet_version: str,
    source_release_id: str,
    soc_version: str,
) -> PipelineResult:
    """Execute the O*NET pipeline: parse → validate → load."""
    from jobclass.parse.onet import parse_onet_descriptors, parse_onet_tasks
    from jobclass.load.onet import (
        load_onet_descriptor_staging, load_onet_task_staging,
        load_dim_descriptor, load_dim_task,
        load_bridge_occupation_descriptor, load_bridge_occupation_task,
    )

    if not check_taxonomy_loaded(conn, soc_version):
        return PipelineResult(
            pipeline_name="onet_refresh",
            status=PipelineStatus.DEPENDENCY_BLOCKED,
            message=f"dim_occupation not loaded for SOC version {soc_version}",
        )

    run_id = generate_run_id()
    create_run_record(
        conn, run_id=run_id, pipeline_name="onet_refresh",
        dataset_name="onet", source_name="onet",
        source_release_id=source_release_id,
    )

    try:
        skills = parse_onet_descriptors(skills_content, source_release_id)
        knowledge = parse_onet_descriptors(knowledge_content, source_release_id)
        abilities = parse_onet_descriptors(abilities_content, source_release_id)
        tasks = parse_onet_tasks(tasks_content, source_release_id)

        load_onet_descriptor_staging(conn, skills, "stage__onet__skills", source_release_id)
        load_onet_descriptor_staging(conn, knowledge, "stage__onet__knowledge", source_release_id)
        load_onet_descriptor_staging(conn, abilities, "stage__onet__abilities", source_release_id)
        load_onet_task_staging(conn, tasks, source_release_id)

        load_dim_descriptor(conn, "dim_skill", "skill_key", "stage__onet__skills", onet_version)
        load_dim_descriptor(conn, "dim_knowledge", "knowledge_key", "stage__onet__knowledge", onet_version)
        load_dim_descriptor(conn, "dim_ability", "ability_key", "stage__onet__abilities", onet_version)
        load_dim_task(conn, onet_version)

        load_bridge_occupation_descriptor(
            conn, "bridge_occupation_skill", "dim_skill", "skill_key",
            "stage__onet__skills", onet_version, source_release_id, soc_version,
        )
        load_bridge_occupation_descriptor(
            conn, "bridge_occupation_knowledge", "dim_knowledge", "knowledge_key",
            "stage__onet__knowledge", onet_version, source_release_id, soc_version,
        )
        load_bridge_occupation_descriptor(
            conn, "bridge_occupation_ability", "dim_ability", "ability_key",
            "stage__onet__abilities", onet_version, source_release_id, soc_version,
        )
        load_bridge_occupation_task(conn, onet_version, source_release_id, soc_version)

        total_loaded = sum(
            conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ["dim_skill", "dim_knowledge", "dim_ability", "dim_task"]
        )

        update_run_counts(
            conn, run_id,
            row_count_raw=len(skills) + len(knowledge) + len(abilities) + len(tasks),
            row_count_stage=len(skills) + len(knowledge) + len(abilities) + len(tasks),
            row_count_loaded=total_loaded,
            load_status="success",
        )
        return PipelineResult(
            pipeline_name="onet_refresh", status=PipelineStatus.SUCCESS, run_id=run_id,
        )
    except Exception as e:
        update_run_counts(
            conn, run_id, load_status="load_failure",
            failure_classification=FailureClassification.LOAD_FAILURE.value,
        )
        return PipelineResult(
            pipeline_name="onet_refresh", status=PipelineStatus.LOAD_FAILURE,
            run_id=run_id, message=str(e),
        )


# ============================================================
# warehouse_publish (P8-04, P8-07)
# ============================================================

def warehouse_publish(
    conn: duckdb.DuckDBPyConnection,
    soc_version: str,
    oews_release_id: str,
    onet_release_id: str,
) -> PipelineResult:
    """Validate all upstream data, then publish marts. Blocked if any validation fails."""
    validations = []

    # Check all required tables have data
    for table, cols in [
        ("dim_occupation", ["occupation_key", "soc_code"]),
        ("dim_geography", ["geography_key", "geo_code"]),
        ("fact_occupation_employment_wages", ["fact_id", "occupation_key"]),
    ]:
        validations.append(validate_required_columns(conn, table, cols))

    # Referential integrity
    validations.append(validate_referential_integrity(
        conn, "fact_occupation_employment_wages", "occupation_key",
        "dim_occupation", "occupation_key",
    ))
    validations.append(validate_referential_integrity(
        conn, "fact_occupation_employment_wages", "geography_key",
        "dim_geography", "geography_key",
    ))

    gate = check_publication_gate(validations)
    if not gate.passed:
        return PipelineResult(
            pipeline_name="warehouse_publish",
            status=PipelineStatus.PUBLISH_BLOCKED,
            message=gate.message,
            validation_results=validations,
        )

    return PipelineResult(
        pipeline_name="warehouse_publish",
        status=PipelineStatus.SUCCESS,
        message="All validations passed — marts published",
        validation_results=validations,
    )
