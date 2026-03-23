# Phased Release Plan — Release 1

This document is the work-tracking artifact for the JobClass pipeline. Each task has a status, requirement traceability, and timestamps updated as work proceeds.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Traces To (requirement IDs), Started, Completed

---

## Phase 1: Project Foundation

Establish repository structure, tech stack, database, and development tooling. Everything downstream depends on this phase.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | P1-01 | Define and create project directory structure (src/, tests/, config/, scripts/, etc.) | — | 2026-03-23 12:30 | 2026-03-23 12:31 |
| `[X]` | P1-02 | Select and document tech stack (Python version, database engine, key libraries) | — | 2026-03-23 12:30 | 2026-03-23 12:31 |
| `[X]` | P1-03 | Initialize Python project (pyproject.toml or setup.cfg, dependency management) | — | 2026-03-23 12:31 | 2026-03-23 12:32 |
| `[X]` | P1-04 | Configure linting and formatting (ruff/black, pre-commit hooks) | — | 2026-03-23 12:32 | 2026-03-23 12:33 |
| `[X]` | P1-05 | Set up test framework (pytest, directory layout, conftest scaffolding) | — | 2026-03-23 12:32 | 2026-03-23 12:33 |
| `[X]` | P1-06 | Create database and apply initial schema migration framework | — | 2026-03-23 12:33 | 2026-03-23 12:34 |
| `[X]` | P1-07 | Create base configuration module (environment handling, paths, constants) | NFR-1 | 2026-03-23 12:34 | 2026-03-23 12:36 |
| `[X]` | P1-08 | Create logging module with structured output | FR-6.9 | 2026-03-23 12:34 | 2026-03-23 12:36 |
| `[X]` | P1-09 | Create `raw/` storage directory structure with path-builder utility | FR-1.5 | 2026-03-23 12:34 | 2026-03-23 12:36 |
| `[X]` | P1-10 | Add .gitignore for raw data, database files, virtual environments | — | 2026-03-23 12:34 | 2026-03-23 12:36 |

---

## Phase 2: Extraction Framework & Run Manifest

Build the manifest-driven download system and run-tracking infrastructure. Required before any pipeline can execute.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | P2-01 | Design and create source manifest schema (YAML/JSON) with all R1 source entries | FR-1.8, DL-2 | 2026-03-23 12:40 | 2026-03-23 12:42 |
| `[X]` | P2-02 | Populate source manifest: SOC hierarchy and definitions | FR-1.1, FR-1.8 | 2026-03-23 12:40 | 2026-03-23 12:42 |
| `[X]` | P2-03 | Populate source manifest: OEWS national and state | FR-1.2, FR-1.8 | 2026-03-23 12:40 | 2026-03-23 12:42 |
| `[X]` | P2-04 | Populate source manifest: O*NET domains (skills, knowledge, abilities, tasks, occupation data) | FR-1.3, FR-1.8 | 2026-03-23 12:40 | 2026-03-23 12:42 |
| `[X]` | P2-05 | Build HTTP download module with metadata capture (headers, status, timestamp) | FR-1.7 | 2026-03-23 12:42 | 2026-03-23 12:45 |
| `[X]` | P2-06 | Implement SHA-256 checksum computation on downloaded artifacts | FR-1.6 | 2026-03-23 12:42 | 2026-03-23 12:45 |
| `[X]` | P2-07 | Implement raw storage writer enforcing path convention `raw/{source}/{dataset}/{release_id}/{run_id}/{filename}` | FR-1.5, NFR-2 | 2026-03-23 12:42 | 2026-03-23 12:45 |
| `[X]` | P2-08 | Implement release version detection from source metadata or parsed content | FR-1.9 | 2026-03-23 12:42 | 2026-03-23 12:45 |
| `[X]` | P2-09 | Create `run_manifest` database table | FR-6.1, FR-6.2 | 2026-03-23 12:44 | 2026-03-23 12:46 |
| `[X]` | P2-10 | Build run manifest creation logic (run_id, pipeline_name, dataset_name, source_name, source_url, source_release_id, downloaded_at, parser_name, parser_version, raw_checksum) | FR-6.1, FR-6.2, OR-6 | 2026-03-23 12:44 | 2026-03-23 12:46 |
| `[X]` | P2-11 | Build manifest-driven extraction orchestrator that reads manifest entries and executes download → checksum → store → register | FR-1.5, FR-1.6, FR-1.7, FR-1.8 | 2026-03-23 12:44 | 2026-03-23 12:46 |
| `[X]` | P2-12 | Implement transient download failure retry with configurable backoff | NFR-7 | 2026-03-23 12:44 | 2026-03-23 12:46 |
| `[X]` | P2-13 | Write unit tests for download module, checksum, path builder, and manifest reader | — | 2026-03-23 12:46 | 2026-03-23 12:50 |

---

## Phase 3: SOC Taxonomy Pipeline

First pipeline to build — occupation dimension is the backbone for all downstream loading.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | P3-01 | Analyze SOC source file format (structure, sheets, encoding, edge cases) | FR-2.1 | 2026-03-23 12:52 | 2026-03-23 12:53 |
| `[X]` | P3-02 | Build SOC hierarchy parser: extract code, title, level, parent link | FR-2.1 | 2026-03-23 12:52 | 2026-03-23 12:55 |
| `[X]` | P3-03 | Build SOC definitions parser: extract code and definition text | FR-2.1 | 2026-03-23 12:52 | 2026-03-23 12:55 |
| `[X]` | P3-04 | Create `stage__soc__hierarchy` table with standardized schema | FR-2.5, FR-2.6, FR-2.9 | 2026-03-23 12:55 | 2026-03-23 12:56 |
| `[X]` | P3-05 | Create `stage__soc__definitions` table with standardized schema | FR-2.5, FR-2.6, FR-2.9 | 2026-03-23 12:55 | 2026-03-23 12:56 |
| `[X]` | P3-06 | Build staging loader: SOC hierarchy (snake_case, explicit types, source_release_id, parser_version) | FR-2.5, FR-2.6, FR-2.8 | 2026-03-23 12:56 | 2026-03-23 12:58 |
| `[X]` | P3-07 | Build staging loader: SOC definitions | FR-2.5, FR-2.6, FR-2.8 | 2026-03-23 12:56 | 2026-03-23 12:58 |
| `[X]` | P3-08 | Implement SOC structural validations: file presence, required columns, minimum row counts, grain uniqueness | FR-3.1, FR-3.2 | 2026-03-23 12:58 | 2026-03-23 12:59 |
| `[X]` | P3-09 | Implement SOC semantic validation: hierarchy completeness — every leaf has path to major group | FR-3.5 | 2026-03-23 12:59 | 2026-03-23 13:00 |
| `[X]` | P3-10 | Create `dim_occupation` table (surrogate key, business key: soc_code + soc_version, all suggested fields) | FR-4.1 | 2026-03-23 12:56 | 2026-03-23 12:56 |
| `[X]` | P3-11 | Build `dim_occupation` loader with version-aware insert (new row on classification change, historical retention) | FR-4.1 | 2026-03-23 12:56 | 2026-03-23 12:58 |
| `[X]` | P3-12 | Create `bridge_occupation_hierarchy` table (parent-child per classification version) | FR-4.2 | 2026-03-23 12:56 | 2026-03-23 12:56 |
| `[X]` | P3-13 | Build `bridge_occupation_hierarchy` loader | FR-4.2 | 2026-03-23 12:56 | 2026-03-23 12:58 |
| `[X]` | P3-14 | Update run manifest with row_count_raw, row_count_stage, row_count_loaded, load_status | FR-6.3, FR-6.4 | 2026-03-23 12:58 | 2026-03-23 12:58 |
| `[X]` | P3-15 | Write parser unit tests with representative SOC source samples | — | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | P3-16 | Write grain uniqueness tests for stage and dim tables | FR-3.2 | 2026-03-23 13:00 | 2026-03-23 13:05 |

---

## Phase 4: OEWS Employment & Wages Pipeline

Introduces `dim_geography`, `dim_industry`, and the primary fact table. Depends on Phase 3 for occupation conformance.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P4-01 | Analyze OEWS national source file format (columns, sheets, encoding, suppressed values) | FR-2.2 | | |
| `[ ]` | P4-02 | Analyze OEWS state source file format and confirm schema alignment with national | FR-2.3 | | |
| `[ ]` | P4-03 | Build OEWS national file parser: standardize occupation code, estimate period, geography, employment, wage fields | FR-2.2 | | |
| `[ ]` | P4-04 | Build OEWS state file parser with same output schema as national | FR-2.3 | | |
| `[ ]` | P4-05 | Create `stage__bls__oews_national` table | FR-2.5, FR-2.6, FR-2.9 | | |
| `[ ]` | P4-06 | Create `stage__bls__oews_state` table | FR-2.5, FR-2.6, FR-2.9 | | |
| `[ ]` | P4-07 | Build staging loaders: OEWS national and state (snake_case, explicit types, null preservation, source_release_id, parser_version) | FR-2.5, FR-2.6, FR-2.7, FR-2.8, FM-4 | | |
| `[ ]` | P4-08 | Create `dim_geography` table (surrogate key, business key: geo_type + geo_code + source_release_id) | FR-4.3 | | |
| `[ ]` | P4-09 | Build `dim_geography` loader with append-on-definition-change behavior | FR-4.3, FM-3 | | |
| `[ ]` | P4-10 | Create `dim_industry` table (surrogate key, business key: naics_code + naics_version) | FR-4.4 | | |
| `[ ]` | P4-11 | Build `dim_industry` loader with append-on-revision behavior | FR-4.4 | | |
| `[ ]` | P4-12 | Create `fact_occupation_employment_wages` table with full grain and all suggested fields | FR-4.5 | | |
| `[ ]` | P4-13 | Build fact loader: enforce composite grain, separate release time from reference time, retain source_dataset | FR-4.5, FR-4.10, FR-4.11 | | |
| `[ ]` | P4-14 | Implement idempotent loading: rerun same dataset-version produces no duplicates | FR-4.9, OR-5 | | |
| `[ ]` | P4-15 | Implement OEWS structural validations: file presence, required columns, expected sheets, min row counts, grain uniqueness | FR-3.1, FR-3.2 | | |
| `[ ]` | P4-16 | Implement OEWS semantic validations: every occupation code maps to active `dim_occupation`, every geography code maps to `dim_geography` | FR-3.3, FR-3.4 | | |
| `[ ]` | P4-17 | Implement OEWS temporal validations: version monotonicity, append-only fact behavior | FR-3.6, FR-3.7 | | |
| `[ ]` | P4-18 | Implement OEWS drift detection: row-count shifts, measure deltas vs. prior release | FR-3.8, FR-3.9 | | |
| `[ ]` | P4-19 | Update run manifest with row counts, load status, failure classification | FR-6.3, FR-6.4 | | |
| `[ ]` | P4-20 | Write parser unit tests with representative OEWS source samples | — | | |
| `[ ]` | P4-21 | Write referential integrity tests: facts reference valid dimension rows | FR-3.3, FR-3.4 | | |
| `[ ]` | P4-22 | Write grain uniqueness tests for staging and fact tables | FR-3.2 | | |

---

## Phase 5: O*NET Semantic Pipeline

Loads descriptor dimensions and bridge tables. Depends on Phase 3 for occupation conformance.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P5-01 | Analyze O*NET source file formats (skills, knowledge, abilities, tasks, occupation data) | FR-2.4 | | |
| `[ ]` | P5-02 | Build O*NET skills parser | FR-2.4 | | |
| `[ ]` | P5-03 | Build O*NET knowledge parser | FR-2.4 | | |
| `[ ]` | P5-04 | Build O*NET abilities parser | FR-2.4 | | |
| `[ ]` | P5-05 | Build O*NET tasks parser | FR-2.4 | | |
| `[ ]` | P5-06 | Create staging tables: `stage__onet__skills`, `stage__onet__knowledge`, `stage__onet__abilities`, `stage__onet__tasks` | FR-2.5, FR-2.6, FR-2.9 | | |
| `[ ]` | P5-07 | Build staging loaders for all four O*NET domains (snake_case, explicit types, null semantics, source_release_id, parser_version) | FR-2.5, FR-2.6, FR-2.7, FR-2.8 | | |
| `[ ]` | P5-08 | Create `dim_skill` table and loader | FR-4.6 | | |
| `[ ]` | P5-09 | Create `dim_knowledge` table and loader | FR-4.6 | | |
| `[ ]` | P5-10 | Create `dim_ability` table and loader | FR-4.6 | | |
| `[ ]` | P5-11 | Create `dim_task` table and loader | FR-4.6 | | |
| `[ ]` | P5-12 | Create `bridge_occupation_skill` table and loader | FR-4.7, NFR-5 | | |
| `[ ]` | P5-13 | Create `bridge_occupation_knowledge` table and loader | FR-4.7, NFR-5 | | |
| `[ ]` | P5-14 | Create `bridge_occupation_ability` table and loader | FR-4.7, NFR-5 | | |
| `[ ]` | P5-15 | Create `bridge_occupation_task` table and loader | FR-4.7, NFR-5 | | |
| `[ ]` | P5-16 | Implement O*NET structural validations: required columns, grain uniqueness per domain | FR-3.1, FR-3.2 | | |
| `[ ]` | P5-17 | Implement O*NET semantic validation: every occupation code maps to active `dim_occupation` | FR-3.3 | | |
| `[ ]` | P5-18 | Implement O*NET–SOC version alignment check; mark unmapped rows, block semantic marts if misaligned | FM-5 | | |
| `[ ]` | P5-19 | Implement idempotent loading for all O*NET tables | FR-4.9, OR-5 | | |
| `[ ]` | P5-20 | Update run manifest with row counts, load status, failure classification | FR-6.3, FR-6.4 | | |
| `[ ]` | P5-21 | Write parser unit tests with representative O*NET source samples | — | | |
| `[ ]` | P5-22 | Write referential integrity tests: bridges reference valid dimension rows | FR-3.3 | | |
| `[ ]` | P5-23 | Write grain uniqueness tests for staging, dimension, and bridge tables | FR-3.2 | | |

---

## Phase 6: Validation Framework & Failure Handling

Consolidate validation logic into a reusable framework. Refactor pipeline-specific validators from Phases 3–5 into shared components.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P6-01 | Extract reusable structural validation module (file presence, required columns, sheet verification, min row counts) | FR-3.1 | | |
| `[ ]` | P6-02 | Extract reusable grain uniqueness validation module (parameterized by table and business key columns) | FR-3.2 | | |
| `[ ]` | P6-03 | Extract reusable referential integrity validation module (parameterized by fact/bridge table and target dimension) | FR-3.3, FR-3.4 | | |
| `[ ]` | P6-04 | Build temporal validation module: version monotonicity check | FR-3.6 | | |
| `[ ]` | P6-05 | Build temporal validation module: append-only mutation check | FR-3.7 | | |
| `[ ]` | P6-06 | Build drift detection module: schema change detection between releases | FR-3.8 | | |
| `[ ]` | P6-07 | Build drift detection module: row-count shift and measure delta detection | FR-3.9 | | |
| `[ ]` | P6-08 | Implement failure classification enum: download_failure, source_format_failure, schema_drift_failure, validation_failure, load_failure, publish_blocked | FR-3.10, FR-6.4 | | |
| `[ ]` | P6-09 | Implement publication-blocking gate: validation failure prevents mart refresh | FR-3.10, FR-5.6 | | |
| `[ ]` | P6-10 | Handle schema drift failure mode: fail fast, classify, preserve raw, block publication | FM-1 | | |
| `[ ]` | P6-11 | Handle partial/corrupted source failure mode: retain raw, mark run incomplete, block downstream | FM-6 | | |
| `[ ]` | P6-12 | Handle material delta failure mode: emit delta report, do not silently accept | FM-7 | | |
| `[ ]` | P6-13 | Refactor Phase 3–5 validators to use shared framework modules | — | | |
| `[ ]` | P6-14 | Write unit tests for each reusable validation module | — | | |

---

## Phase 7: Observability & Run Reporting

Complete the run metadata system and reporting outputs. Builds on run manifest from Phase 2 and validation framework from Phase 6.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P7-01 | Extend run manifest with completion fields: row_count_raw, row_count_stage, row_count_loaded, load_status, failure_classification, validation_summary | FR-6.3, FR-6.4 | | |
| `[ ]` | P7-02 | Build row-count delta reporter (current vs. prior successful run per dataset) | FR-6.5 | | |
| `[ ]` | P7-03 | Build schema drift report emitter (per dataset, per release) | FR-6.6 | | |
| `[ ]` | P7-04 | Build top measure delta reporter (per dataset) | FR-6.7 | | |
| `[ ]` | P7-05 | Build reconciliation summary reporter (where published totals are available) | FR-6.8 | | |
| `[ ]` | P7-06 | Build run inspection view: single run fully inspectable from metadata alone | FR-6.9 | | |
| `[ ]` | P7-07 | Generate example run manifest output for portfolio deliverable | DL-4 | | |
| `[ ]` | P7-08 | Generate example validation report output for portfolio deliverable | DL-5 | | |
| `[ ]` | P7-09 | Write tests for all report emitters | — | | |

---

## Phase 8: Orchestration

Wire individual pipelines into dependency-aware execution with idempotence and publish gating.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P8-01 | Implement `taxonomy_refresh` pipeline (extract → parse → validate → load SOC) | OR-1 | | |
| `[ ]` | P8-02 | Implement `oews_refresh` pipeline (extract → parse → validate → load OEWS) | OR-1 | | |
| `[ ]` | P8-03 | Implement `onet_refresh` pipeline (extract → parse → validate → load O*NET) | OR-1 | | |
| `[ ]` | P8-04 | Implement `warehouse_publish` pipeline (validate all → publish marts) | OR-1, OR-4 | | |
| `[ ]` | P8-05 | Enforce dependency: `taxonomy_refresh` completes before occupation conformance on new SOC version | OR-2, NFR-8 | | |
| `[ ]` | P8-06 | Allow independent execution of `oews_refresh` and `onet_refresh` | OR-3, NFR-9 | | |
| `[ ]` | P8-07 | Implement publish gating: `warehouse_publish` blocked unless all upstream validations pass | OR-4, OR-7, FR-5.6 | | |
| `[ ]` | P8-08 | Verify dataset-level idempotence across all pipelines | OR-5, FR-4.9 | | |
| `[ ]` | P8-09 | Ensure run manifest is created at pipeline start and updated at completion | OR-6 | | |
| `[ ]` | P8-10 | Implement no-retry policy on semantic validation failure | NFR-7 | | |
| `[ ]` | P8-11 | Write integration tests for pipeline dependency ordering | — | | |
| `[ ]` | P8-12 | Write idempotent rerun integration tests (same version, no duplicates) | FR-4.9 | | |

---

## Phase 9: Analyst Marts

Build the five analyst-facing views. Depends on Phases 3–5 (data loaded) and Phase 8 (publish gating).

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P9-01 | Build `occupation_summary` mart: one row per occupation with hierarchy fields and profile attributes | FR-5.1 | | |
| `[ ]` | P9-02 | Build `occupation_wages_by_geography` mart: employment and wage measures by occupation and geography | FR-5.2 | | |
| `[ ]` | P9-03 | Build `occupation_skill_profile` mart: occupation-to-skill relationships from current O*NET version | FR-5.3 | | |
| `[ ]` | P9-04 | Build `occupation_task_profile` mart: occupation-to-task relationships for selected occupations | FR-5.4 | | |
| `[ ]` | P9-05 | Build `occupation_similarity_seeded` mart: similarity view based on shared skill/task structures | FR-5.5 | | |
| `[ ]` | P9-06 | Enforce publish gating: marts only refresh after upstream validation succeeds | FR-5.6, OR-7 | | |
| `[ ]` | P9-07 | Write query-level tests: verify grain, join correctness, and lineage traceability for each mart | — | | |
| `[ ]` | P9-08 | Populate example marts with real data for portfolio deliverable | DL-8 | | |

---

## Phase 10: Employment Projections (Optional R1)

Optional fourth source. Architecturally simple if Phases 1–8 are complete.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P10-01 | Populate source manifest entry for Employment Projections | FR-1.4, FR-1.8 | | |
| `[ ]` | P10-02 | Analyze Employment Projections source file format | FR-1.4 | | |
| `[ ]` | P10-03 | Build projections parser: normalize projection cycle, base year, target year, occupation code | FR-2.4 | | |
| `[ ]` | P10-04 | Create staging table `stage__bls__employment_projections` | FR-2.9 | | |
| `[ ]` | P10-05 | Build staging loader for projections | FR-2.5, FR-2.6, FR-2.8 | | |
| `[ ]` | P10-06 | Create `fact_occupation_projections` table with full grain and suggested fields | FR-4.8 | | |
| `[ ]` | P10-07 | Build fact loader with idempotent append-by-cycle behavior | FR-4.8, FR-4.9 | | |
| `[ ]` | P10-08 | Implement projections validations (structural, semantic, temporal) | FR-3.1, FR-3.2, FR-3.3 | | |
| `[ ]` | P10-09 | Implement `projections_refresh` pipeline | OR-1 | | |
| `[ ]` | P10-10 | Write parser and loader tests | — | | |

---

## Phase 11: End-to-End Integration & Portfolio Deliverables

Final verification and deliverable production. The "Software Developers" worked example from the design document is the integration test.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | P11-01 | Run full end-to-end pipeline for Software Developers occupation (SOC 15-1252) as integration test | Design §18 | | |
| `[ ]` | P11-02 | Verify: occupation code maps to active SOC version after load | FR-3.3 | | |
| `[ ]` | P11-03 | Verify: OEWS fact row is unique at declared grain | FR-3.2 | | |
| `[ ]` | P11-04 | Verify: O*NET bridge rows reference valid descriptor dimensions | FR-3.3 | | |
| `[ ]` | P11-05 | Verify: analyst query returns state-level wage distribution for Software Developers | Design §18 | | |
| `[ ]` | P11-06 | Verify: analyst query returns core skills and tasks for Software Developers | Design §18 | | |
| `[ ]` | P11-07 | Run historical regression tests against known published totals | — | | |
| `[ ]` | P11-08 | Run idempotent rerun tests: full pipeline re-execution produces no duplicates | FR-4.9 | | |
| `[ ]` | P11-09 | Generate warehouse schema documentation | DL-6 | | |
| `[ ]` | P11-10 | Create analyst notebook or dashboard with sample queries | DL-7 | | |
| `[ ]` | P11-11 | Final review: confirm all DL-1 through DL-8 deliverables are present and complete | DL-1 through DL-8 | | |

---

## Phase Summary

| Phase | Description | Task Count | Dependencies |
|-------|-------------|------------|--------------|
| 1 | Project Foundation | 10 | None |
| 2 | Extraction Framework & Run Manifest | 13 | Phase 1 |
| 3 | SOC Taxonomy Pipeline | 16 | Phase 2 |
| 4 | OEWS Employment & Wages Pipeline | 22 | Phases 2, 3 |
| 5 | O*NET Semantic Pipeline | 23 | Phases 2, 3 |
| 6 | Validation Framework & Failure Handling | 14 | Phases 3, 4, 5 |
| 7 | Observability & Run Reporting | 9 | Phases 2, 6 |
| 8 | Orchestration | 12 | Phases 3, 4, 5, 6 |
| 9 | Analyst Marts | 8 | Phases 3, 4, 5, 8 |
| 10 | Employment Projections (Optional R1) | 10 | Phases 2, 3, 6 |
| 11 | End-to-End Integration & Deliverables | 11 | All prior phases |
| **Total** | | **148** | |

---

## Dependency Graph

```
Phase 1 ──► Phase 2 ──┬──► Phase 3 ──┬──► Phase 4 ──┐
                       │              │              │
                       │              ├──► Phase 5 ──┤
                       │              │              │
                       │              ▼              ▼
                       │         Phase 6 ◄───────────┘
                       │              │
                       ▼              ▼
                    Phase 7 ◄── Phase 6
                       │              │
                       │              ▼
                       │         Phase 8
                       │              │
                       │              ▼
                       │         Phase 9
                       │
                       ├──► Phase 10 (optional, after Phase 3 + 6)
                       │
                       └──────────────────► Phase 11 (all)
```

Phases 4 and 5 may execute in parallel after Phase 3 completes.
