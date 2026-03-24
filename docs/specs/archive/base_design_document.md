# Labor Market Occupation Pipeline Design Document

## 1. Why This Project Exists

This project exists to demonstrate how I approach real-world data work when the source domain is messy, versioned, and semantically rich. It is intended to show source-driven pipeline design, schema discipline, reproducible ingestion, version-aware modeling, operational validation, and the ability to turn public raw data into a durable analytical asset.

The specific domain is labor-market occupation data. I chose it because it forces several important engineering decisions: separating formal occupation taxonomies from employer-specific titles, handling release-driven source drift, preserving historical comparability, and modeling both quantitative facts and semantic descriptors in a way that supports analytics rather than just storage.

This is not meant to be a one-off ETL exercise. It is meant to be an example of how I design a system that can be trusted, extended, and operated over time.

## 2. Purpose

This pipeline builds a durable, queryable labor-market occupation warehouse centered on formal occupation data rather than employer-specific job titles.

The core design assumption is that occupation is the stable external key, while titles, roles, classes, and functions are local business metadata that should map onto the occupation layer rather than replace it.

Release 1 ingests three primary federal data products:

SOC for the occupation hierarchy.

OEWS for employment and wage facts.

O*NET for semantic descriptors such as skills, knowledge, abilities, tasks, and work context.

An optional fourth source, Employment Projections, is included in the design and can be added early with minimal architectural change.

## 3. Business Questions Supported in Release 1

Release 1 is designed to answer a small but useful set of concrete questions.

How many people work in a given occupation nationally and by state?

What are the wage distributions for a given occupation across geographies?

What occupations belong to a broader family such as computer and mathematical occupations?

What skills, tasks, knowledge areas, and abilities are associated with a given occupation?

Which occupations appear similar based on semantic descriptors such as tasks and skills?

What data quality, source version, and release lineage produced a given analytical result?

These questions are intentionally chosen to demonstrate analytical usefulness, source integration, and modeling discipline in the first release.

## 4. Audience and Design Bias

This design is written for a data engineer, analytics engineer, technical lead, or hiring manager evaluating how I structure a production-minded data system.

The design is biased toward explicit grain, immutable raw capture, deterministic processing, idempotent loading, historical versioning, conformed dimensions, and clear separation between source truth and local business interpretation.

## 5. Scope

### 5.1 In scope for release 1

Release 1 includes SOC hierarchy ingest and normalization, OEWS ingest for national and state tables, O*NET ingest for selected core descriptor domains, a warehouse schema with source lineage and version tracking, repeatable refresh orchestration, testing and validation, and analyst-ready marts.

Release 1 intentionally stops short of solving the entire labor-market modeling problem. It focuses on building the correct backbone.

### 5.2 Recommended additions for release 1.1

Metro and nonmetro OEWS tables.

National industry-specific OEWS tables.

Area definition files for geography rollups.

Employment Projections ingest.

Additional OEWS supporting files such as STEM and education requirement outputs.

### 5.3 Deliberately not solved yet

Internal HR job architecture is not modeled in release 1 because employer-specific job classes, functions, and levels are local concepts that would dilute the clarity of the external occupation backbone.

Job title normalization is deferred because title ambiguity is a separate problem that deserves either curated rules or a classifier, not a rushed placeholder mapping.

International harmonization is deferred because crosswalk design across taxonomies such as SOC and ISCO introduces comparability complexity that is not needed to demonstrate the core pipeline pattern.

Real-time APIs are deferred because this project is intended to show correctness, repeatability, and data product design, not low-latency serving.

## 6. Source Contributions and Risks

### 6.1 SOC

SOC provides the authoritative occupation hierarchy and classification key. It defines the levels and parent-child structure used throughout the warehouse.

Primary contribution:
formal taxonomy backbone.

Primary risks:
classification revisions, changes in definitions, and crosswalk complexity when mixing historical periods.

### 6.2 OEWS

OEWS provides occupational employment counts and wage measures.

Primary contribution:
quantitative fact layer.

Primary risks:
release-driven schema variation, geography definition changes, suppressed or missing values, and comparability issues across historical periods.

Important modeling decision:
OEWS is treated as published statistical estimates, not transactional headcount.

### 6.3 O*NET

O*NET provides semantic descriptors attached to occupations.

Primary contribution:
semantic enrichment layer.

Primary risks:
version drift, domain-level file changes, and occupation-code mismatches relative to the active classification context.

Important modeling decision:
O*NET is modeled as structured descriptors and bridges, not appended text.

### 6.4 Employment Projections

Employment Projections provide outlook-oriented data by occupation.

Primary contribution:
forward-looking fact layer.

Primary risks:
projection-cycle comparability and ambiguity between projected change and realized historical change.

## 7. Design Tradeoffs

### 7.1 Occupation over title

This pipeline uses formal occupation as the external analytical truth and treats job title as a later mapping input. I am making this choice because titles are unstable, local, and often politically shaped by employer conventions. Occupation is the better conformed key.

### 7.2 Immutable raw over replace-in-place ingestion

Raw source artifacts are stored immutably. I am choosing this because reproducibility and auditability matter more than saving storage. A pipeline that cannot reconstruct what it ingested is weak as both an analytical system and a portfolio artifact.

### 7.3 Split semantic bridges over generic EAV

O*NET domains are modeled as separate bridge tables rather than one generalized attribute-value table. I am choosing this because the separate-table design is easier to validate, easier to explain, easier to query, and less error-prone for downstream analysts. The cost is more tables. That is acceptable here.

### 7.4 Release time separate from reference time

The design explicitly separates source publication metadata from business reference periods. I am choosing this because a May 2024 OEWS release and a 2024 estimate year are not the same thing. Blending them creates avoidable confusion and weakens lineage.

### 7.5 Layered warehouse over direct analyst-facing source tables

The pipeline includes raw, staging, core warehouse, and marts. I am choosing this because each layer has a different responsibility and protects against a different class of problems. Directly querying parsed source tables would be faster to build, but weaker operationally and less defensible analytically.

## 8. Target Architecture

The architecture has four layers, each with a specific purpose and explicit constraints.

### 8.1 Landing / Raw

Purpose:
capture exactly what was downloaded.

Protects against:
loss of lineage, inability to reparse, accidental historical overwrite, ambiguity about what source content was used.

Forbidden here:
business logic, conformance logic, enrichment, destructive updates.

Required metadata:
original file name, source URL, download timestamp, checksum, content type, source release label, parser version assigned later, and run identifier.

### 8.2 Standardized Staging

Purpose:
parse heterogeneous source files into predictable relational structures.

Protects against:
format instability, parser complexity leaking into the warehouse, inconsistent null and date handling.

Forbidden here:
business-friendly denormalization, semantic rollups, source-to-source reconciliation logic, analyst-facing derived fields.

Required work:
standardized column names, explicit typing, explicit null semantics, source-version extraction, dataset-level record lineage.

### 8.3 Core Warehouse

Purpose:
define the analytical truth model.

Protects against:
source-specific naming leakage, ambiguous joins, repeated hierarchy derivation, inconsistent semantic attachment patterns.

Forbidden here:
source-format assumptions, presentation-only reshaping, ad hoc query optimizations that obscure grain.

Required work:
conformed dimensions, conformed facts, bridge tables, version-aware joins, stable warehouse naming.

### 8.4 Marts / Semantic Views

Purpose:
optimize repeated analyst and portfolio use cases.

Protects against:
analysts rebuilding the same logic repeatedly, inconsistent downstream query patterns, unnecessary exposure to warehouse complexity.

Forbidden here:
new business logic that bypasses warehouse truth, remapping of raw source semantics without traceability.

Required work:
denormalized, query-friendly views tied to specific questions.

## 9. Canonical Data Model

All major tables declare grain, business key, key policy, and version behavior.

### 9.1 dim_occupation

Grain:
one row per occupation code per classification version.

Business key:
soc_code plus soc_version.

Key policy:
surrogate warehouse key plus retained business key.

Version behavior:
new rows inserted for classification changes; prior rows retained historically.

Suggested fields:
occupation_key, soc_code, occupation_title, occupation_level, occupation_level_name, parent_soc_code, major_group_code, minor_group_code, broad_occupation_code, detailed_occupation_code, occupation_definition, soc_version, is_leaf, effective_start_date, effective_end_date, is_current, source_release_id.

### 9.2 bridge_occupation_hierarchy

Grain:
one row per parent-child relationship per classification version.

Business key:
parent_soc_code plus child_soc_code plus soc_version.

Key policy:
natural composite key is acceptable.

Version behavior:
append on taxonomy change.

Suggested fields:
parent_occupation_key, child_occupation_key, relationship_level, soc_version, source_release_id.

### 9.3 dim_geography

Grain:
one row per geography code per source definition set.

Business key:
geo_type plus geo_code plus source_release_id.

Key policy:
surrogate warehouse key plus retained business key.

Version behavior:
append on geography-definition change.

Suggested fields:
geography_key, geo_type, geo_code, geo_name, state_fips, county_fips, msa_code, is_cross_state, effective_start_date, effective_end_date, is_current, source_release_id.

### 9.4 dim_industry

Grain:
one row per NAICS code per NAICS version.

Business key:
naics_code plus naics_version.

Key policy:
surrogate warehouse key plus retained business key.

Version behavior:
append on NAICS revision.

Suggested fields:
industry_key, naics_code, industry_title, industry_level, parent_naics_code, naics_version, effective_start_date, effective_end_date, is_current.

### 9.5 fact_occupation_employment_wages

Grain:
one row per estimate period, geography, industry slice, ownership slice, occupation, and source dataset.

Business key:
reference_period plus geography_key plus industry_key plus ownership_code plus occupation_key plus source_dataset.

Key policy:
surrogate fact key optional; composite business grain enforced.

Version behavior:
append by source release and reference period; do not overwrite prior published releases.

Suggested fields:
fact_id, reference_period, estimate_year, geography_key, industry_key, ownership_code, occupation_key, employment_count, employment_rse, jobs_per_1000, location_quotient, mean_hourly_wage, mean_annual_wage, median_hourly_wage, median_annual_wage, p10_hourly_wage, p25_hourly_wage, p75_hourly_wage, p90_hourly_wage, source_dataset, source_release_id, load_timestamp.

### 9.6 dim_skill

Grain:
one row per skill identifier per O*NET version.

Business key:
skill_id plus source_version.

Key policy:
surrogate warehouse key plus retained business key.

Version behavior:
append on descriptor revision.

Suggested fields:
skill_key, skill_id, skill_name, skill_description, source_version, is_current.

### 9.7 bridge_occupation_skill

Grain:
one row per occupation, skill, scale type, and source version.

Business key:
occupation_key plus skill_key plus scale_type plus source_version.

Key policy:
composite business key.

Version behavior:
append by O*NET version.

Suggested fields:
occupation_key, skill_key, scale_type, data_value, n, standard_error, source_version, source_release_id.

### 9.8 dim_knowledge

Grain:
one row per knowledge identifier per O*NET version.

Business key:
knowledge_id plus source_version.

Key policy:
surrogate warehouse key plus retained business key.

Version behavior:
append by descriptor revision.

### 9.9 bridge_occupation_knowledge

Grain:
one row per occupation, knowledge item, scale type, and source version.

Business key:
occupation_key plus knowledge_key plus scale_type plus source_version.

Version behavior:
append by O*NET version.

### 9.10 dim_ability

Grain:
one row per ability identifier per O*NET version.

Business key:
ability_id plus source_version.

Version behavior:
append by descriptor revision.

### 9.11 bridge_occupation_ability

Grain:
one row per occupation, ability item, scale type, and source version.

Business key:
occupation_key plus ability_key plus scale_type plus source_version.

Version behavior:
append by O*NET version.

### 9.12 dim_task

Grain:
one row per task identifier per O*NET version.

Business key:
task_id plus source_version.

Version behavior:
append by descriptor revision.

### 9.13 bridge_occupation_task

Grain:
one row per occupation, task, and source version.

Business key:
occupation_key plus task_key plus source_version.

Version behavior:
append by O*NET version.

Suggested fields:
occupation_key, task_key, task_type, importance, frequency, source_version, source_release_id.

### 9.14 fact_occupation_projections

Grain:
one row per projection cycle and occupation.

Business key:
projection_cycle plus occupation_key.

Key policy:
surrogate fact key optional; grain enforced at load time.

Version behavior:
append by projection cycle.

Suggested fields:
projection_cycle, occupation_key, base_year, projection_year, employment_base, employment_projected, employment_change_abs, employment_change_pct, annual_openings, education_category, training_category, work_experience_category, source_release_id.

## 10. Concrete Implementation View

This project needs enough implementation detail to be buildable and reviewable.

### 10.1 Dataset identifiers

Use stable internal dataset identifiers:

soc_hierarchy

soc_definitions

oews_national

oews_state

oews_metro

oews_industry_national

onet_skills

onet_knowledge

onet_abilities

onet_tasks

onet_occupation_data

bls_employment_projections

bls_area_definitions

### 10.2 Raw storage naming

Use raw object paths in this form:

raw/source_name/dataset_name/source_release_id/run_id/original_file_name

Example:

raw/bls/oews_state/2024.05/2026-03-23T09-15-00Z/state_M2024_dl.xlsx

### 10.3 Staging table naming

Use stage__source__dataset convention.

Examples:

stage__bls__oews_state

stage__bls__oews_national

stage__onet__skills

stage__soc__hierarchy

### 10.4 Core table naming

Use dim_, fact_, and bridge_ prefixes consistently.

Examples:

dim_occupation

dim_geography

dim_industry

dim_skill

fact_occupation_employment_wages

bridge_occupation_skill

### 10.5 Run manifest

Every run should create a manifest record with:

run_id

pipeline_name

dataset_name

source_name

source_url

source_release_id

downloaded_at

parser_name

parser_version

raw_checksum

row_count_raw

row_count_stage

row_count_loaded

load_status

failure_classification

validation_summary

### 10.6 Naming rules

All warehouse columns use snake_case.

All date-time fields use UTC timestamps.

All versioned sources expose both source_release_id and source_version where they differ.

All facts retain source_dataset to preserve lineage across dataset families.

## 11. Pipeline Flow

### 11.1 Extract

The extractor is declarative and driven by a source manifest.

Each manifest entry includes source_name, dataset_name, dataset_url, expected_format, refresh_cadence, parser_name, version_detection_rule, enabled_flag, and destination path rule.

Extraction steps:
download artifact, capture HTTP metadata, compute checksum, store raw file, register source snapshot, create run manifest, and emit parse work.

The extractor must not assume stable file names. Release identification must come from source metadata or parsed content when possible.

### 11.2 Parse

Parsing logic is dataset-specific.

SOC parsing extracts classification levels, codes, titles, parent-child links, and definitions.

OEWS parsing standardizes columns, estimate periods, geography codes, occupation codes, and wage field semantics.

O*NET parsing loads each domain independently, normalizes occupation and descriptor identifiers, and separates dimensions from bridges.

Projection parsing normalizes projection cycle, base year, target year, and occupation code.

### 11.3 Validate

Validation is a first-class product requirement.

Structural validations check file presence, checksum capture, required columns, expected sheets or tabs, minimum row counts, and uniqueness at the declared grain.

Semantic validations check valid occupation mapping, valid geography mapping, valid hierarchy completeness, and reconciliation of published totals where applicable.

Temporal validations check version monotonicity, release preservation, and append-only behavior for historical data.

Drift validations check schema change, unexpected row-count shifts, abnormal null growth, and large measure deltas.

### 11.4 Load

Loading is idempotent at the dataset-version grain.

The load sequence is:
register snapshot, load stage, execute validations, merge dimensions, insert facts and bridges, publish marts only after successful validation, and emit quality artifacts.

Historical fact sets and versioned semantic descriptors are append-and-version only.

## 12. Observability

Observability is not just logging. It is the ability to explain what ran, what changed, and why a result should be trusted.

Each run will emit:

run metadata keyed by run_id,

dataset-level audit records,

parser version capture,

row-count deltas against prior successful runs,

schema drift detection results,

reconciliation summaries,

top measure deltas by dataset,

load status by target table,

failure classification.

Failure classifications should include at least:
download_failure,
source_format_failure,
schema_drift_failure,
validation_failure,
load_failure,
publish_blocked.

A reviewer should be able to inspect a single run and understand exactly what happened without reading pipeline code.

## 13. Testing Strategy

Validation and testing are separate.

Testing verifies the pipeline logic itself.

The project should include parser unit tests, schema contract tests, declared-grain uniqueness tests, referential integrity tests, historical regression tests on known published totals, and idempotent rerun tests.

At minimum:

parser tests verify representative source files parse correctly.

schema contract tests fail when required columns disappear or change type.

grain tests fail on duplicate business keys.

referential tests fail when facts or bridges point to missing dimensions.

historical regression tests compare selected known totals against approved reference outputs.

idempotent rerun tests verify that rerunning the same dataset version does not create duplicate output.

This section matters because the project is intended to show methodology, not just structure.

## 14. Failure Modes and Operational Risks

This pipeline should assume source behavior will be imperfect.

If source schema drift occurs, the run should fail fast at staging, classify the failure, preserve the raw artifact, and block warehouse publication until the parser is updated or the schema change is explicitly approved.

If a SOC revision introduces crosswalk instability, the pipeline should preserve both classification versions, store explicit crosswalk tables, and keep comparable-history marts separate from as-published-history marts.

If geography definitions change, the pipeline should append a new geography definition set rather than mutate old geography rows. Historical facts should remain tied to the area definitions current at publication time.

If OEWS publishes suppressed or missing values, the pipeline should preserve source null semantics explicitly rather than impute values.

If O*NET and SOC versions do not align cleanly, the pipeline should load the raw versioned semantic data, mark unmapped rows, and block derived semantic marts until the mapping condition is resolved.

If a source release is partial or corrupted, the pipeline should retain the raw download, mark the run as incomplete, and prevent downstream publication.

If published totals change materially relative to the prior release, the pipeline should emit a delta report rather than silently treating that difference as normal.

## 15. Orchestration Strategy

This project requires dependency-aware orchestration, but the important point is not the orchestration brand. The important point is deterministic dependency boundaries.

Logical pipelines:
taxonomy_refresh,
oews_refresh,
onet_refresh,
projections_refresh,
warehouse_publish.

Dependencies:
SOC must complete before occupation conformance when a new SOC version appears.

OEWS and O*NET may run independently.

Publication depends on successful validation of all datasets included in the target release.

Required orchestration behavior:
dataset-level idempotence,
retry on transient download failure,
no retry on semantic validation failure without intervention,
run manifest creation at pipeline start,
publish gating on validation success.

## 16. Historical Versioning and Backfill

There are two distinct time concepts.

Source release time identifies what was published and when it was captured.

Business reference time identifies the period the data describes.

The design preserves both.

Backfill should occur in layers.

First load the active SOC baseline.

Then load OEWS for a selected comparability window.

Then load O*NET for the current version, unless semantic history is explicitly in scope.

Then load Employment Projections for recent cycles.

Comparability must be made explicit.

The system should support both as-published history and comparable trend history.

As-published history preserves what was originally released under the taxonomy and definitions active at that time.

Comparable trend history uses explicit crosswalk logic and version-aware marts to support longitudinal analysis across classification changes.

Those are separate products and should not be conflated.

## 17. Analyst and Portfolio Marts

The first marts should be concrete and reviewable.

occupation_summary presents one row per occupation with hierarchy fields and selected profile attributes.

occupation_wages_by_geography presents employment and wage measures by occupation and geography.

occupation_skill_profile presents occupation-to-skill relationships using current O*NET version data.

occupation_task_profile presents occupation-to-task relationships for selected occupations.

occupation_similarity_seeded presents an initial view that allows similarity experiments using shared skill and task structures.

These marts make the project inspectable without forcing a reviewer to reconstruct joins from the warehouse core.

## 18. End-to-End Example

Use Software Developers as a worked example.

The extractor downloads the relevant OEWS national and state files, the active SOC hierarchy source, and the selected O*NET domain files.

Each file is stored immutably in raw storage under a release-specific path and registered in the run manifest with checksum and parser version.

The parser normalizes occupation codes, extracts the SOC hierarchy row for the relevant occupation, standardizes OEWS wage and employment fields, and loads O*NET skill and task rows tied to the occupation.

Validation confirms that the occupation code maps to the active SOC version, that the OEWS fact row is unique at its declared grain, and that the O*NET bridge rows reference valid descriptor dimensions.

The load process inserts the occupation row if needed, inserts the OEWS fact rows for national and state slices, inserts the skill and task bridge rows for the selected O*NET version, and publishes the occupation_summary and occupation_skill_profile marts.

A final analyst query can now answer:
what is the current state-level wage distribution for Software Developers, and which core skills and task descriptors are attached to that occupation in the current semantic layer?

That example demonstrates the full pipeline pattern from acquisition to analytical output.

## 19. Deliverables for Portfolio Review

A reviewer should be able to inspect more than the design document.

This project should expose:

the design document,

the source manifest,

sample extraction and parsing code,

example run manifests,

example validation and reconciliation reports,

warehouse schema documentation,

a small analyst notebook or dashboard,

one or two example marts populated with real data.

That set of deliverables better demonstrates data analysis skill, tool creation skill, and engineering methodology than the design document alone.

## 20. Practical Recommendations From Experience

Do not design the warehouse around title text.

Do not place semantic descriptors into comma-separated arrays.

Do not let source-specific naming leak into the warehouse model.

Do not overwrite historical releases.

Do not mix publication metadata with reference-period metadata.

Do not blur the boundary between as-published history and comparable-history analytics.

Do not claim semantic extensibility without exposing at least one concrete downstream semantic mart.

## 21. Future Directions

The following items are intentionally deferred but fit naturally into the architecture.

Add a title normalization and title-to-occupation mapping layer using curated rules first and a classifier later.

Add metro and industry-specific marts once geography and industry expansion is complete.

Add richer semantic downstream products such as occupation clustering, skill-gap scoring, and transition scoring once the initial descriptor bridges are stable.

Add explicit workflow artifacts for parser evolution, schema approval, and release certification if the project grows into a multi-maintainer system.

Add international harmonization with ISCO once the project needs cross-national comparability and the crosswalk problem is worth the complexity.

Add stronger implementation packaging, such as a published repository layout and exact deployment instructions, if the project is being handed off for collaborative development.

## 22. Final Recommendation

Build the pipeline around occupation as the external truth key, preserve source artifacts immutably, separate publication time from business reference time, and model semantic enrichment as structured data rather than descriptive text.

That produces a system that is analytically useful, operationally defensible, and strong as a portfolio example because it shows design judgment, implementation readiness, and methodological discipline.
