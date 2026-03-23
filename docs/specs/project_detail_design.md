# Project Detail Design — Downstream User Requirements

This document distills the design specification (`design_document_v1.md`) into concrete requirements organized by what downstream users need from the system. It is intended as the direct input for two derivative documents: a **Phased Release Plan** and a **Test Plan**.

---

## 1. Downstream User Profiles

### 1.1 Analyst

Consumes marts and warehouse views. Needs: correct grain, clear joins, documented lineage, predictable refresh cadence, and queryable occupation-centric data without reconstructing source logic.

### 1.2 Data Engineer (Operator)

Runs and monitors the pipeline. Needs: idempotent execution, observable run metadata, classified failures, deterministic dependency ordering, and the ability to diagnose a failed run without reading pipeline code.

### 1.3 Reviewer / Evaluator

Inspects the system as a portfolio artifact. Needs: visible methodology, traceable design decisions, sample outputs, validation evidence, and a clear path from raw source to analytical result.

---

## 2. Functional Requirements

### FR-1: Source Acquisition

| ID | Requirement | User |
|----|-------------|------|
| FR-1.1 | Download SOC hierarchy and definition files from BLS | Operator |
| FR-1.2 | Download OEWS national and state Excel/CSV files from BLS | Operator |
| FR-1.3 | Download O*NET domain files (skills, knowledge, abilities, tasks, occupation data) | Operator |
| FR-1.4 | Download Employment Projections files from BLS (optional R1) | Operator |
| FR-1.5 | Store every downloaded artifact immutably at `raw/{source}/{dataset}/{release_id}/{run_id}/{filename}` | Operator |
| FR-1.6 | Compute and record SHA-256 checksum for every raw artifact | Operator |
| FR-1.7 | Capture HTTP metadata (headers, response code, download timestamp) per download | Operator |
| FR-1.8 | Drive extraction from a declarative source manifest, not hardcoded URLs | Operator |
| FR-1.9 | Detect source release version from metadata or parsed content, not from file name alone | Operator |

### FR-2: Parsing and Staging

| ID | Requirement | User |
|----|-------------|------|
| FR-2.1 | Parse SOC files into hierarchy rows with code, title, level, parent link, and definition | Analyst, Operator |
| FR-2.2 | Parse OEWS national files into standardized rows with occupation code, estimate period, geography, employment, and wage fields | Analyst |
| FR-2.3 | Parse OEWS state files with the same schema as national | Analyst |
| FR-2.4 | Parse O*NET skill, knowledge, ability, and task files into separate staging tables per domain | Analyst |
| FR-2.5 | Standardize all column names to snake_case | Analyst, Operator |
| FR-2.6 | Apply explicit typing (numeric, date, text) at staging; reject ambiguous implicit casts | Operator |
| FR-2.7 | Preserve source null semantics — do not impute suppressed or missing values | Analyst |
| FR-2.8 | Attach source_release_id and parser_version to every staging record | Operator |
| FR-2.9 | Write staging tables using `stage__{source}__{dataset}` naming | Operator |

### FR-3: Validation

| ID | Requirement | User |
|----|-------------|------|
| FR-3.1 | Structural: verify file presence, required columns, expected sheets/tabs, minimum row counts | Operator |
| FR-3.2 | Structural: verify uniqueness at the declared grain for every staging and core table | Operator, Analyst |
| FR-3.3 | Semantic: verify every occupation code in facts and bridges maps to an active `dim_occupation` row | Analyst |
| FR-3.4 | Semantic: verify every geography code in OEWS facts maps to `dim_geography` | Analyst |
| FR-3.5 | Semantic: verify SOC hierarchy completeness — every leaf has a path to major group | Analyst |
| FR-3.6 | Temporal: verify version monotonicity — new loads do not predate existing loads for the same dataset | Operator |
| FR-3.7 | Temporal: verify append-only behavior — historical fact rows are never mutated | Operator, Analyst |
| FR-3.8 | Drift: detect schema changes (added/removed/retyped columns) between releases | Operator |
| FR-3.9 | Drift: detect abnormal row-count shifts and large measure deltas vs. prior release | Operator |
| FR-3.10 | Block warehouse publication when any validation fails; classify the failure | Operator |

### FR-4: Core Warehouse Loading

| ID | Requirement | User |
|----|-------------|------|
| FR-4.1 | Load `dim_occupation` — one row per SOC code per classification version, surrogate key, retained business key | Analyst |
| FR-4.2 | Load `bridge_occupation_hierarchy` — one row per parent-child pair per classification version | Analyst |
| FR-4.3 | Load `dim_geography` — one row per geo code per source definition set | Analyst |
| FR-4.4 | Load `dim_industry` — one row per NAICS code per NAICS version | Analyst |
| FR-4.5 | Load `fact_occupation_employment_wages` — grain: estimate period × geography × industry × ownership × occupation × source dataset | Analyst |
| FR-4.6 | Load `dim_skill`, `dim_knowledge`, `dim_ability`, `dim_task` — one row per descriptor ID per O*NET version | Analyst |
| FR-4.7 | Load `bridge_occupation_skill`, `bridge_occupation_knowledge`, `bridge_occupation_ability`, `bridge_occupation_task` — one row per occupation × descriptor × scale type × version | Analyst |
| FR-4.8 | Load `fact_occupation_projections` — one row per projection cycle × occupation (optional R1) | Analyst |
| FR-4.9 | Loading must be idempotent at dataset-version grain — rerun produces identical output with no duplicates | Operator |
| FR-4.10 | Separate source release time from business reference time on every fact | Analyst |
| FR-4.11 | Retain `source_dataset` on every fact for cross-dataset lineage | Analyst, Reviewer |

### FR-5: Marts

| ID | Requirement | User |
|----|-------------|------|
| FR-5.1 | `occupation_summary` — one row per occupation with hierarchy fields and profile attributes | Analyst |
| FR-5.2 | `occupation_wages_by_geography` — employment and wage measures by occupation and geography | Analyst |
| FR-5.3 | `occupation_skill_profile` — occupation-to-skill relationships from current O*NET version | Analyst |
| FR-5.4 | `occupation_task_profile` — occupation-to-task relationships for selected occupations | Analyst |
| FR-5.5 | `occupation_similarity_seeded` — initial similarity view based on shared skill/task structures | Analyst |
| FR-5.6 | Marts publish only after all upstream validations pass | Operator |

### FR-6: Observability and Run Metadata

| ID | Requirement | User |
|----|-------------|------|
| FR-6.1 | Create a run manifest record at pipeline start with run_id, pipeline_name, dataset_name, source_name, source_url, source_release_id | Operator |
| FR-6.2 | Record downloaded_at, parser_name, parser_version, raw_checksum per run | Operator |
| FR-6.3 | Record row_count_raw, row_count_stage, row_count_loaded per run | Operator |
| FR-6.4 | Record load_status and failure_classification per run | Operator |
| FR-6.5 | Emit row-count deltas against prior successful run | Operator |
| FR-6.6 | Emit schema drift detection results per dataset | Operator |
| FR-6.7 | Emit top measure deltas by dataset | Operator |
| FR-6.8 | Emit reconciliation summaries where published totals are available | Operator, Reviewer |
| FR-6.9 | A single run must be fully inspectable from its metadata alone, without reading code | Operator, Reviewer |

---

## 3. Non-Functional Requirements

| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-1 | All warehouse columns use snake_case; all timestamps UTC | Naming consistency across layers |
| NFR-2 | Raw artifacts are never deleted or overwritten | Reproducibility and audit trail |
| NFR-3 | No business logic in the raw or staging layers | Layer isolation; prevents logic entanglement |
| NFR-4 | No source-specific naming in core warehouse tables | Conformed model independence from source format |
| NFR-5 | O*NET domains modeled as separate bridge tables, not generic EAV | Query clarity, validation simplicity, analyst usability |
| NFR-6 | Historical facts are append-only; prior releases never overwritten | Temporal integrity |
| NFR-7 | Pipeline retries on transient download failure; does not retry on semantic validation failure | Safe failure behavior |
| NFR-8 | SOC must complete before occupation conformance on new classification versions | Dependency correctness |
| NFR-9 | OEWS and O*NET pipelines may run independently | Parallelism where safe |
| NFR-10 | As-published history and comparable-trend history are separate products | Prevents analytical confusion |

---

## 4. Data Model Requirements

### 4.1 Dimensions

| Table | Grain | Business Key | Version Behavior |
|-------|-------|-------------|-----------------|
| `dim_occupation` | SOC code × classification version | soc_code + soc_version | New row on classification change |
| `dim_geography` | Geo code × source definition set | geo_type + geo_code + source_release_id | Append on definition change |
| `dim_industry` | NAICS code × NAICS version | naics_code + naics_version | Append on NAICS revision |
| `dim_skill` | Skill ID × O*NET version | skill_id + source_version | Append on descriptor revision |
| `dim_knowledge` | Knowledge ID × O*NET version | knowledge_id + source_version | Append on descriptor revision |
| `dim_ability` | Ability ID × O*NET version | ability_id + source_version | Append on descriptor revision |
| `dim_task` | Task ID × O*NET version | task_id + source_version | Append on descriptor revision |

### 4.2 Facts

| Table | Grain | Version Behavior |
|-------|-------|-----------------|
| `fact_occupation_employment_wages` | Period × geography × industry × ownership × occupation × source dataset | Append by release and period |
| `fact_occupation_projections` | Projection cycle × occupation | Append by cycle |

### 4.3 Bridges

| Table | Grain | Version Behavior |
|-------|-------|-----------------|
| `bridge_occupation_hierarchy` | Parent code × child code × classification version | Append on taxonomy change |
| `bridge_occupation_skill` | Occupation × skill × scale type × O*NET version | Append by version |
| `bridge_occupation_knowledge` | Occupation × knowledge × scale type × O*NET version | Append by version |
| `bridge_occupation_ability` | Occupation × ability × scale type × O*NET version | Append by version |
| `bridge_occupation_task` | Occupation × task × O*NET version | Append by version |

---

## 5. Failure-Mode Requirements

These define how the system must behave when sources are imperfect.

| ID | Condition | Required Behavior |
|----|-----------|-------------------|
| FM-1 | Source schema drift detected | Fail fast at staging, classify as `schema_drift_failure`, preserve raw artifact, block publication |
| FM-2 | SOC revision introduces crosswalk instability | Preserve both classification versions, store crosswalk table, keep comparable-history marts separate |
| FM-3 | Geography definitions change across releases | Append new definition set; do not mutate old rows; historical facts stay tied to original definitions |
| FM-4 | OEWS publishes suppressed/missing values | Preserve source null semantics explicitly; never impute |
| FM-5 | O*NET and SOC versions do not align | Load raw versioned data, mark unmapped rows, block derived semantic marts until mapping resolved |
| FM-6 | Source release is partial or corrupted | Retain raw download, mark run incomplete, prevent downstream publication |
| FM-7 | Published totals change materially vs. prior release | Emit delta report; do not silently accept |

---

## 6. Orchestration Requirements

| ID | Requirement |
|----|-------------|
| OR-1 | Five logical pipelines: `taxonomy_refresh`, `oews_refresh`, `onet_refresh`, `projections_refresh`, `warehouse_publish` |
| OR-2 | `taxonomy_refresh` must complete before occupation conformance when a new SOC version appears |
| OR-3 | `oews_refresh` and `onet_refresh` may execute independently |
| OR-4 | `warehouse_publish` depends on successful validation of all included datasets |
| OR-5 | Dataset-level idempotence on every pipeline |
| OR-6 | Run manifest created at pipeline start, updated at completion |
| OR-7 | Publish gating: marts only refresh after upstream validation succeeds |

---

## 7. Deliverable Requirements

These define what a reviewer or evaluator must be able to inspect beyond code.

| ID | Deliverable |
|----|-------------|
| DL-1 | Design document |
| DL-2 | Source manifest (declarative extraction configuration) |
| DL-3 | Sample extraction and parsing code |
| DL-4 | Example run manifests |
| DL-5 | Example validation and reconciliation reports |
| DL-6 | Warehouse schema documentation |
| DL-7 | Analyst notebook or dashboard |
| DL-8 | One or two example marts populated with real data |

---

## 8. Scope Boundaries

### In scope for Release 1

- SOC hierarchy ingest and normalization
- OEWS national and state ingest
- O*NET core descriptor domains (skills, knowledge, abilities, tasks)
- Core warehouse schema with lineage and version tracking
- Repeatable refresh orchestration
- Validation framework
- Five analyst-ready marts

### Recommended for Release 1.1

- Metro and nonmetro OEWS tables
- National industry-specific OEWS tables
- Area definition files for geography rollups
- Employment Projections ingest
- Additional OEWS supporting files (STEM, education requirements)

### Explicitly deferred

- Internal HR job architecture / employer-specific job classes
- Job title normalization (requires curated rules or classifier)
- International harmonization (SOC ↔ ISCO crosswalk)
- Real-time serving APIs

---

## 9. Traceability Map

This section links requirements back to the design decisions that produced them, providing context for release and test planning.

| Requirement Area | Governing Design Decision |
|-----------------|--------------------------|
| FR-1 (Acquisition) | Immutable raw over replace-in-place (Design §7.2) |
| FR-2 (Parsing) | Layered warehouse with staging isolation (Design §7.5) |
| FR-3 (Validation) | Validation as first-class product requirement (Design §11.3) |
| FR-4 (Loading) | Release time ≠ reference time (Design §7.4); Idempotent loading (Design §11.4) |
| FR-5 (Marts) | Layered warehouse over direct source tables (Design §7.5) |
| FR-6 (Observability) | Run-level inspectability (Design §12) |
| NFR-5 (Split bridges) | Split semantic bridges over generic EAV (Design §7.3) |
| FM-1–7 (Failure modes) | Operational failure handling (Design §14) |
