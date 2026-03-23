# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Labor market occupation data pipeline that ingests federal data products (SOC, OEWS, O*NET, Employment Projections) into a layered analytical warehouse. The core design principle: **occupation is the stable external key**; job titles, roles, and internal classifications map onto it, not the other way around.

The full design specification lives in `docs/specs/design_document_v1.md`.

## Architecture: Four-Layer Warehouse

1. **Landing/Raw** — Immutable capture of downloaded artifacts. No business logic. Required metadata: file name, source URL, download timestamp, checksum, source release label, run ID.
2. **Standardized Staging** — Parse heterogeneous source files into relational structures. Standardized column names, explicit typing, explicit null semantics. No denormalization or semantic rollups.
3. **Core Warehouse** — Conformed dimensions (`dim_`), facts (`fact_`), and bridges (`bridge_`). Version-aware joins. No source-format assumptions.
4. **Marts** — Denormalized, query-friendly views for specific analytical questions. No new business logic that bypasses warehouse truth.

## Naming Conventions

- **Raw paths**: `raw/{source_name}/{dataset_name}/{source_release_id}/{run_id}/{original_file_name}`
- **Staging tables**: `stage__{source}__{dataset}` (e.g., `stage__bls__oews_state`, `stage__onet__skills`)
- **Core tables**: `dim_`, `fact_`, `bridge_` prefixes (e.g., `dim_occupation`, `fact_occupation_employment_wages`, `bridge_occupation_skill`)
- **Columns**: snake_case everywhere. Date-times in UTC. Versioned sources expose both `source_release_id` and `source_version`.

## Data Sources

| Source | Internal IDs | Role |
|--------|-------------|------|
| SOC | `soc_hierarchy`, `soc_definitions` | Occupation taxonomy backbone |
| OEWS | `oews_national`, `oews_state`, `oews_metro`, `oews_industry_national` | Employment counts and wage measures |
| O*NET | `onet_skills`, `onet_knowledge`, `onet_abilities`, `onet_tasks`, `onet_occupation_data` | Semantic descriptors (skills, tasks, etc.) |
| BLS Projections | `bls_employment_projections` | Forward-looking employment data |

## Key Design Decisions

- **Immutable raw storage**: Never overwrite downloaded artifacts. Reproducibility over storage savings.
- **Split semantic bridges**: O*NET domains get separate bridge tables (not a generic EAV table). More tables is acceptable for clarity.
- **Two time concepts**: Source release time (when published/captured) vs. business reference time (period described). Never conflate them.
- **As-published vs. comparable history**: These are separate analytical products. As-published preserves original taxonomy; comparable history uses crosswalk logic.
- **Idempotent loading**: Re-running the same dataset version must not create duplicates.
- **Fail-fast on schema drift**: Block warehouse publication until parser is updated or change is approved.
- **Preserve source nulls**: Never impute suppressed/missing OEWS values.

## Pipeline Flow

Extract (declarative, manifest-driven) -> Parse (dataset-specific) -> Validate (structural, semantic, temporal, drift) -> Load (idempotent at dataset-version grain)

Logical pipelines: `taxonomy_refresh`, `oews_refresh`, `onet_refresh`, `projections_refresh`, `warehouse_publish`. SOC must complete before occupation conformance; OEWS and O*NET may run independently.

## Testing Strategy

- Parser unit tests on representative source files
- Schema contract tests (fail on missing/changed columns)
- Grain uniqueness tests (fail on duplicate business keys)
- Referential integrity tests (facts/bridges must point to existing dimensions)
- Historical regression tests against known published totals
- Idempotent rerun tests (no duplicate output on re-run)

## Release 1 Scope

In scope: SOC hierarchy, OEWS national + state, O*NET core descriptors, warehouse schema with lineage/version tracking, repeatable orchestration, validation, and five initial marts (`occupation_summary`, `occupation_wages_by_geography`, `occupation_skill_profile`, `occupation_task_profile`, `occupation_similarity_seeded`).

Not in scope: HR job architecture, title normalization, international harmonization, real-time APIs.
