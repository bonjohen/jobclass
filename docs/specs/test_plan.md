# Test Plan — Release 1

This document defines all tests for the JobClass pipeline, aligned phase-by-phase with the [Phased Release Plan](phased_release_plan.md). After refinement, tests will be merged into the release plan as tracked tasks.

---

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

---

## Test Types

| Code | Type | Purpose |
|------|------|---------|
| UNIT | Unit Test | Verify a single function or module in isolation |
| CONTRACT | Schema Contract Test | Fail when required columns disappear or change type |
| GRAIN | Grain Uniqueness Test | Fail on duplicate business keys at declared grain |
| REF | Referential Integrity Test | Fail when facts or bridges point to missing dimensions |
| SEMANTIC | Semantic Validation Test | Verify logical correctness of loaded data (mappings, completeness, nulls) |
| TEMPORAL | Temporal Validation Test | Verify version ordering, append-only behavior, time separation |
| DRIFT | Drift Detection Test | Detect schema changes, row-count shifts, or measure deltas across releases |
| IDEMPOTENT | Idempotent Rerun Test | Verify rerun of same dataset-version produces no duplicates or mutations |
| REGRESSION | Historical Regression Test | Compare loaded values against known published reference totals |
| FAILURE | Failure-Mode Test | Verify correct system behavior under a specific failure condition |
| INTEGRATION | Integration Test | Verify end-to-end flow across multiple modules or pipeline stages |
| QUERY | Query Validation Test | Verify mart output grain, joins, and analytical correctness |

**Columns**: Status, Test ID, Type, Description, Pass Criteria, Traces To (requirement), Validates Task, Started, Completed

---

## Phase 1 Tests: Project Foundation

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T1-01 | UNIT | Configuration module loads defaults and environment overrides correctly | Config object returns expected values for known keys; environment variable overrides take precedence | NFR-1 | P1-07 | 2026-03-23 12:36 | 2026-03-23 12:38 |
| `[X]` | T1-02 | UNIT | Path-builder utility produces correct raw storage paths | Output matches `raw/{source}/{dataset}/{release_id}/{run_id}/{filename}` for all parameter combinations | FR-1.5 | P1-09 | 2026-03-23 12:36 | 2026-03-23 12:38 |
| `[X]` | T1-03 | UNIT | Path-builder rejects missing or empty path components | Raises ValueError for None, empty string, or whitespace in any component | FR-1.5 | P1-09 | 2026-03-23 12:36 | 2026-03-23 12:38 |
| `[X]` | T1-04 | UNIT | Logging module emits structured output with expected fields | Log entries contain timestamp, level, module, and message; timestamp is UTC | FR-6.9, NFR-1 | P1-08 | 2026-03-23 12:36 | 2026-03-23 12:38 |
| `[X]` | T1-05 | UNIT | Database connection and migration framework execute without error | Migration applies cleanly to empty database; rollback succeeds | — | P1-06 | 2026-03-23 12:36 | 2026-03-23 12:38 |

---

## Phase 2 Tests: Extraction Framework & Run Manifest

### Download & Storage

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T2-01 | UNIT | HTTP download module returns content and captures metadata | Response includes body bytes, status code, headers dict, and UTC download timestamp | FR-1.7 | P2-05 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-02 | UNIT | HTTP download module raises on non-2xx status after retries exhausted | After configured retry count, raises DownloadError with status code and URL | FR-1.7, NFR-7 | P2-05, P2-12 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-03 | UNIT | Transient failure retry respects configured backoff and max attempts | 3 consecutive 503s with backoff=2s → retries at ~0s, ~2s, ~4s; 4th failure raises | NFR-7 | P2-12 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-04 | UNIT | SHA-256 checksum computation matches known digest for test file | Checksum of fixed byte content matches precomputed hex digest | FR-1.6 | P2-06 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-05 | UNIT | Raw storage writer creates file at correct path and content is byte-identical | File exists at expected path; reading it back produces identical bytes; checksum matches | FR-1.5, NFR-2 | P2-07 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-06 | UNIT | Raw storage writer does not overwrite existing file at same path | Second write to same path raises or skips (does not silently replace) | NFR-2 | P2-07 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-07 | UNIT | Release version detection extracts version from test metadata/content | Returns expected version string for each supported detection strategy | FR-1.9 | P2-08 | 2026-03-23 12:47 | 2026-03-23 12:50 |

### Source Manifest

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T2-08 | UNIT | Manifest reader parses valid manifest file into structured entries | Each entry has source_name, dataset_name, dataset_url, expected_format, parser_name, enabled flag | FR-1.8 | P2-01 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-09 | UNIT | Manifest reader rejects manifest with missing required fields | Raises validation error identifying the missing field and entry | FR-1.8 | P2-01 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-10 | UNIT | Manifest reader filters disabled entries | Only entries with enabled=true are returned for execution | FR-1.8 | P2-01 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-11 | CONTRACT | SOC manifest entries contain required fields and valid URLs | Entries for soc_hierarchy and soc_definitions exist, have dataset_url, parser_name, and expected_format | FR-1.1 | P2-02 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-12 | CONTRACT | OEWS manifest entries contain required fields and valid URLs | Entries for oews_national and oews_state exist with all required fields | FR-1.2 | P2-03 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-13 | CONTRACT | O*NET manifest entries contain required fields and valid URLs | Entries for onet_skills, onet_knowledge, onet_abilities, onet_tasks exist with all required fields | FR-1.3 | P2-04 | 2026-03-23 12:47 | 2026-03-23 12:50 |

### Run Manifest

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T2-14 | UNIT | Run manifest creation inserts record with all required fields | Record contains run_id, pipeline_name, dataset_name, source_name, source_url, source_release_id, downloaded_at, parser_name, parser_version, raw_checksum | FR-6.1, FR-6.2 | P2-09, P2-10 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-15 | UNIT | Run manifest run_id is unique across concurrent creations | 100 concurrent manifest creations produce 100 distinct run_ids | FR-6.1 | P2-10 | 2026-03-23 12:47 | 2026-03-23 12:50 |
| `[X]` | T2-16 | INTEGRATION | Extraction orchestrator executes full sequence: read manifest → download → checksum → store → register | For a test manifest entry: raw file exists at correct path, checksum recorded in run manifest, all metadata fields populated | FR-1.5, FR-1.6, FR-1.7, FR-1.8 | P2-11 | 2026-03-23 12:47 | 2026-03-23 12:50 |

---

## Phase 3 Tests: SOC Taxonomy Pipeline

### Parser Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T3-01 | UNIT | SOC hierarchy parser extracts correct code, title, level, and parent link from representative sample | Parsed rows match expected values for at least: one major group (XX-0000), one minor group, one broad occupation, one detailed occupation | FR-2.1 | P3-02 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-02 | UNIT | SOC hierarchy parser handles edge cases: codes with trailing zeros, "All Other" categories | Edge-case rows parse without error; codes and titles preserved exactly | FR-2.1 | P3-02 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-03 | UNIT | SOC definitions parser extracts code and definition text from representative sample | Each row has non-null soc_code and occupation_definition; code format matches `\d{2}-\d{4}` | FR-2.1 | P3-03 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-04 | UNIT | SOC parsers apply snake_case column names and explicit types | All output column names are snake_case; code columns are text; level columns are integer | FR-2.5, FR-2.6 | P3-02, P3-03 | 2026-03-23 13:00 | 2026-03-23 13:05 |

### Staging Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T3-05 | CONTRACT | `stage__soc__hierarchy` has all required columns with correct types | Table exists; columns include soc_code (text), occupation_title (text), occupation_level (integer), parent_soc_code (text), source_release_id (text), parser_version (text) | FR-2.5, FR-2.6, FR-2.8, FR-2.9 | P3-04, P3-06 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-06 | CONTRACT | `stage__soc__definitions` has all required columns with correct types | Table exists; columns include soc_code (text), occupation_definition (text), source_release_id (text), parser_version (text) | FR-2.5, FR-2.6, FR-2.8, FR-2.9 | P3-05, P3-07 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-07 | GRAIN | `stage__soc__hierarchy` has no duplicate business keys | Zero rows returned by: `SELECT soc_code, source_release_id, COUNT(*) ... HAVING COUNT(*) > 1` | FR-3.2 | P3-08, P3-16 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-08 | GRAIN | `stage__soc__definitions` has no duplicate business keys | Zero duplicates on soc_code + source_release_id | FR-3.2 | P3-08, P3-16 | 2026-03-23 13:00 | 2026-03-23 13:05 |

### Structural & Semantic Validations

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T3-09 | SEMANTIC | SOC hierarchy is complete: every leaf occupation has a path to its major group | For every row where is_leaf=true, recursive parent traversal reaches a row with occupation_level = major group | FR-3.5 | P3-09 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-10 | SEMANTIC | Every parent_soc_code in hierarchy references an existing soc_code | Zero orphan parent references within the same source_release_id | FR-3.5 | P3-09 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-11 | SEMANTIC | SOC staging row count meets minimum threshold | Row count ≥ 800 (2018 SOC has 867 detailed occupations) | FR-3.1 | P3-08 | 2026-03-23 13:00 | 2026-03-23 13:05 |

### Dimension & Bridge Loading Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T3-12 | GRAIN | `dim_occupation` has no duplicate business keys (soc_code + soc_version) | Zero duplicates on business key | FR-3.2 | P3-10, P3-16 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-13 | CONTRACT | `dim_occupation` contains all required fields from data model | Table has: occupation_key, soc_code, occupation_title, occupation_level, occupation_level_name, parent_soc_code, soc_version, is_leaf, is_current, source_release_id | FR-4.1 | P3-10 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-14 | SEMANTIC | `dim_occupation` surrogate keys are unique and non-null | Zero null occupation_key values; zero duplicate occupation_key values | FR-4.1 | P3-11 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-15 | SEMANTIC | `dim_occupation` version-aware insert: loading a new SOC version creates new rows without mutating prior rows | After loading version B, all version A rows remain identical (bitwise compare); version B rows added | FR-4.1 | P3-11 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-16 | GRAIN | `bridge_occupation_hierarchy` has no duplicate business keys (parent + child + soc_version) | Zero duplicates on composite key | FR-3.2 | P3-12, P3-16 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-17 | REF | `bridge_occupation_hierarchy` parent and child keys reference valid `dim_occupation` rows | Zero orphan references in parent_occupation_key or child_occupation_key | FR-3.3 | P3-13 | 2026-03-23 13:00 | 2026-03-23 13:05 |
| `[X]` | T3-18 | UNIT | Run manifest updated with row counts and load_status after SOC load | run_manifest record for SOC run has non-null row_count_raw, row_count_stage, row_count_loaded, and load_status = 'success' | FR-6.3, FR-6.4 | P3-14 | 2026-03-23 13:00 | 2026-03-23 13:05 |

---

## Phase 4 Tests: OEWS Employment & Wages Pipeline

### Parser Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T4-01 | UNIT | OEWS national parser extracts occupation code, estimate period, geography, employment, and wage fields from representative sample | Parsed rows match expected values for at least 3 known occupations; wage fields are numeric or null | FR-2.2 | P4-03 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-02 | UNIT | OEWS state parser produces same output schema as national parser | Column names and types are identical between national and state parser output | FR-2.3 | P4-04 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-03 | UNIT | OEWS parsers preserve suppressed values as null, not as zero or placeholder | For a row with known BLS suppression markers (**, #, N/A), wage fields parse to null | FR-2.7, FM-4 | P4-03, P4-04 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-04 | UNIT | OEWS parsers apply snake_case names and explicit types | All column names are snake_case; employment is numeric; wage fields are numeric; codes are text | FR-2.5, FR-2.6 | P4-03, P4-04 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-05 | UNIT | OEWS parsers attach source_release_id and parser_version to every row | Every output row has non-null source_release_id and parser_version | FR-2.8 | P4-07 | 2026-03-23 13:16 | 2026-03-23 13:22 |

### Staging Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T4-06 | CONTRACT | `stage__bls__oews_national` has all required columns with correct types | Table exists with expected column names and types | FR-2.5, FR-2.6, FR-2.9 | P4-05 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-07 | CONTRACT | `stage__bls__oews_state` has all required columns with correct types | Table exists; schema matches national staging table | FR-2.5, FR-2.6, FR-2.9 | P4-06 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-08 | GRAIN | `stage__bls__oews_national` has no duplicate rows at declared grain | Zero duplicates on occupation_code + estimate_period + geography_code + industry_code + ownership_code + source_release_id | FR-3.2 | P4-15, P4-22 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-09 | GRAIN | `stage__bls__oews_state` has no duplicate rows at declared grain | Zero duplicates on same composite key as national | FR-3.2 | P4-15, P4-22 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-10 | SEMANTIC | OEWS staging row counts meet minimum thresholds | National ≥ 800 rows; state ≥ 25,000 rows | FR-3.1 | P4-15 | 2026-03-23 13:16 | 2026-03-23 13:22 |

### Dimension Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T4-11 | GRAIN | `dim_geography` has no duplicate business keys (geo_type + geo_code + source_release_id) | Zero duplicates on business key | FR-3.2 | P4-08 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-12 | CONTRACT | `dim_geography` contains all required fields from data model | Table has: geography_key, geo_type, geo_code, geo_name, state_fips, is_current, source_release_id | FR-4.3 | P4-08 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-13 | SEMANTIC | `dim_geography` append-on-change: new definition set does not mutate existing rows | After loading release B definitions, all release A rows remain identical | FR-4.3, FM-3 | P4-09 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-14 | GRAIN | `dim_industry` has no duplicate business keys (naics_code + naics_version) | Zero duplicates on business key | FR-3.2 | P4-10 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-15 | CONTRACT | `dim_industry` contains all required fields from data model | Table has: industry_key, naics_code, industry_title, naics_version, is_current | FR-4.4 | P4-10 | 2026-03-23 13:16 | 2026-03-23 13:22 |

### Fact Table Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T4-16 | GRAIN | `fact_occupation_employment_wages` has no duplicate rows at declared grain | Zero duplicates on reference_period + geography_key + industry_key + ownership_code + occupation_key + source_dataset | FR-3.2 | P4-12, P4-22 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-17 | CONTRACT | `fact_occupation_employment_wages` contains all required fields from data model | Table has all suggested fields including source_release_id, source_dataset, load_timestamp | FR-4.5 | P4-12 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-18 | SEMANTIC | Fact table separates source release time from business reference time | source_release_id and reference_period/estimate_year are independently populated; no rows where they are conflated | FR-4.10 | P4-13 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-19 | SEMANTIC | Fact table retains source_dataset on every row | Zero null source_dataset values | FR-4.11 | P4-13 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-20 | REF | Every occupation_key in fact table references valid `dim_occupation` row | Zero orphan occupation_key values | FR-3.3 | P4-16, P4-21 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-21 | REF | Every geography_key in fact table references valid `dim_geography` row | Zero orphan geography_key values | FR-3.4 | P4-16, P4-21 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-22 | REF | Every industry_key in fact table references valid `dim_industry` row | Zero orphan industry_key values | FR-3.4 | P4-16 | 2026-03-23 13:16 | 2026-03-23 13:22 |

### Temporal & Drift Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T4-23 | TEMPORAL | Version monotonicity: new OEWS load has source_release_id ≥ all existing release IDs for same dataset | No release ID regression detected | FR-3.6 | P4-17 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-24 | TEMPORAL | Append-only: loading new OEWS release does not modify any prior-release fact rows | Checksum of prior-release fact rows before and after load are identical | FR-3.7 | P4-17 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-25 | DRIFT | Schema drift detection: adding a column to OEWS source triggers detection | Drift detector reports the added column name and type | FR-3.8 | P4-18 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-26 | DRIFT | Schema drift detection: removing a required column from OEWS source triggers detection | Drift detector reports the missing column | FR-3.8 | P4-18 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-27 | DRIFT | Row-count shift detection: ±20% row count change vs. prior release triggers alert | Detector emits warning with absolute and percentage change | FR-3.9 | P4-18 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-28 | DRIFT | Measure delta detection: ≥15% change in mean_annual_wage for a major occupation group triggers alert | Detector emits report identifying the occupation group and delta magnitude | FR-3.9 | P4-18 | 2026-03-23 13:16 | 2026-03-23 13:22 |

### Idempotence Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T4-29 | IDEMPOTENT | Rerun OEWS national load for same release: no duplicate fact rows | Row count before and after rerun is identical; no new rows inserted | FR-4.9 | P4-14 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-30 | IDEMPOTENT | Rerun OEWS state load for same release: no duplicate fact rows | Row count before and after rerun is identical | FR-4.9 | P4-14 | 2026-03-23 13:16 | 2026-03-23 13:22 |
| `[X]` | T4-31 | IDEMPOTENT | Rerun OEWS load for same release: dim_geography not duplicated | Geography row count unchanged after rerun | FR-4.9 | P4-14 | 2026-03-23 13:16 | 2026-03-23 13:22 |

---

## Phase 5 Tests: O*NET Semantic Pipeline

### Parser Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T5-01 | UNIT | O*NET skills parser extracts occupation code, skill ID, skill name, scale type, data value from representative sample | Parsed rows match expected values for at least 3 known occupation-skill pairs | FR-2.4 | P5-02 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-02 | UNIT | O*NET knowledge parser extracts expected fields from representative sample | Parsed rows match expected values for known occupation-knowledge pairs | FR-2.4 | P5-03 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-03 | UNIT | O*NET abilities parser extracts expected fields from representative sample | Parsed rows match expected values for known occupation-ability pairs | FR-2.4 | P5-04 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-04 | UNIT | O*NET tasks parser extracts expected fields from representative sample | Parsed rows match expected values for known occupation-task pairs | FR-2.4 | P5-05 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-05 | UNIT | All O*NET parsers apply snake_case names and explicit types | All column names snake_case; data_value is numeric; codes are text | FR-2.5, FR-2.6 | P5-02 through P5-05 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-06 | UNIT | All O*NET parsers attach source_release_id and parser_version | Every output row has non-null source_release_id and parser_version | FR-2.8 | P5-07 | 2026-03-23 13:38 | 2026-03-23 13:42 |

### Staging Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T5-07 | CONTRACT | `stage__onet__skills` has all required columns with correct types | Table exists with expected columns and types | FR-2.9 | P5-06 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-08 | CONTRACT | `stage__onet__knowledge` has all required columns with correct types | Table exists with expected columns and types | FR-2.9 | P5-06 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-09 | CONTRACT | `stage__onet__abilities` has all required columns with correct types | Table exists with expected columns and types | FR-2.9 | P5-06 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-10 | CONTRACT | `stage__onet__tasks` has all required columns with correct types | Table exists with expected columns and types | FR-2.9 | P5-06 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-11 | GRAIN | `stage__onet__skills` has no duplicate rows at declared grain | Zero duplicates on occupation_code + skill_id + scale_type + source_release_id | FR-3.2 | P5-16, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-12 | GRAIN | `stage__onet__knowledge` has no duplicate rows at declared grain | Zero duplicates on occupation_code + knowledge_id + scale_type + source_release_id | FR-3.2 | P5-16, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-13 | GRAIN | `stage__onet__abilities` has no duplicate rows at declared grain | Zero duplicates on occupation_code + ability_id + scale_type + source_release_id | FR-3.2 | P5-16, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-14 | GRAIN | `stage__onet__tasks` has no duplicate rows at declared grain | Zero duplicates on occupation_code + task_id + source_release_id | FR-3.2 | P5-16, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |

### Dimension Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T5-15 | GRAIN | `dim_skill` has no duplicate business keys (skill_id + source_version) | Zero duplicates | FR-3.2 | P5-08, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-16 | GRAIN | `dim_knowledge` has no duplicate business keys (knowledge_id + source_version) | Zero duplicates | FR-3.2 | P5-09, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-17 | GRAIN | `dim_ability` has no duplicate business keys (ability_id + source_version) | Zero duplicates | FR-3.2 | P5-10, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-18 | GRAIN | `dim_task` has no duplicate business keys (task_id + source_version) | Zero duplicates | FR-3.2 | P5-11, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-19 | CONTRACT | All O*NET dimension tables contain required fields from data model | Each dim has surrogate key, descriptor ID, name, source_version, is_current | FR-4.6 | P5-08 through P5-11 | 2026-03-23 13:38 | 2026-03-23 13:42 |

### Bridge Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T5-20 | GRAIN | `bridge_occupation_skill` has no duplicate business keys | Zero duplicates on occupation_key + skill_key + scale_type + source_version | FR-3.2 | P5-12, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-21 | GRAIN | `bridge_occupation_knowledge` has no duplicate business keys | Zero duplicates on occupation_key + knowledge_key + scale_type + source_version | FR-3.2 | P5-13, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-22 | GRAIN | `bridge_occupation_ability` has no duplicate business keys | Zero duplicates on occupation_key + ability_key + scale_type + source_version | FR-3.2 | P5-14, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-23 | GRAIN | `bridge_occupation_task` has no duplicate business keys | Zero duplicates on occupation_key + task_key + source_version | FR-3.2 | P5-15, P5-23 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-24 | REF | `bridge_occupation_skill` occupation_key references valid `dim_occupation` | Zero orphans | FR-3.3 | P5-12, P5-22 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-25 | REF | `bridge_occupation_skill` skill_key references valid `dim_skill` | Zero orphans | FR-3.3 | P5-12, P5-22 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-26 | REF | `bridge_occupation_knowledge` references valid `dim_occupation` and `dim_knowledge` | Zero orphans on both keys | FR-3.3 | P5-13, P5-22 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-27 | REF | `bridge_occupation_ability` references valid `dim_occupation` and `dim_ability` | Zero orphans on both keys | FR-3.3 | P5-14, P5-22 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-28 | REF | `bridge_occupation_task` references valid `dim_occupation` and `dim_task` | Zero orphans on both keys | FR-3.3 | P5-15, P5-22 | 2026-03-23 13:38 | 2026-03-23 13:42 |

### Semantic & Version Alignment Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T5-29 | SEMANTIC | O*NET–SOC version alignment: all O*NET occupation codes map to active `dim_occupation` rows | Zero unmapped occupation codes when versions are aligned | FM-5 | P5-17, P5-18 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-30 | SEMANTIC | O*NET–SOC version misalignment: unmapped rows are marked, semantic marts blocked | When O*NET version references codes absent from active SOC, those rows are flagged; semantic mart publication is blocked | FM-5 | P5-18 | 2026-03-23 13:38 | 2026-03-23 13:42 |

### Idempotence Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T5-31 | IDEMPOTENT | Rerun O*NET skills load for same version: no duplicate dim or bridge rows | Row counts in dim_skill and bridge_occupation_skill unchanged after rerun | FR-4.9 | P5-19 | 2026-03-23 13:38 | 2026-03-23 13:42 |
| `[X]` | T5-32 | IDEMPOTENT | Rerun O*NET full load for same version: all tables unchanged | Row counts across all 8 O*NET tables unchanged after rerun | FR-4.9 | P5-19 | 2026-03-23 13:38 | 2026-03-23 13:42 |

---

## Phase 6 Tests: Validation Framework & Failure Handling

### Reusable Module Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T6-01 | UNIT | Structural validator: detects missing required column | Given a table missing column X from the required set, returns failure naming X | FR-3.1 | P6-01 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-02 | UNIT | Structural validator: detects column type change | Given a column that changed from integer to text, returns failure with old and new type | FR-3.1 | P6-01 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-03 | UNIT | Structural validator: passes when all required columns present with correct types | Returns success for a table matching the expected schema | FR-3.1 | P6-01 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-04 | UNIT | Structural validator: detects row count below minimum threshold | Given a threshold of 100 and a table with 50 rows, returns failure | FR-3.1 | P6-01 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-05 | UNIT | Grain validator: detects duplicate business keys | Given a table with 2 rows sharing the same composite key, returns failure identifying the key values | FR-3.2 | P6-02 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-06 | UNIT | Grain validator: passes on unique business keys | Given a table with all-unique composite keys, returns success | FR-3.2 | P6-02 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-07 | UNIT | Referential integrity validator: detects orphan foreign keys | Given a fact table with an occupation_key absent from dim_occupation, returns failure listing the orphan key(s) | FR-3.3, FR-3.4 | P6-03 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-08 | UNIT | Referential integrity validator: passes when all keys resolve | Returns success when all foreign keys exist in the target dimension | FR-3.3, FR-3.4 | P6-03 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-09 | UNIT | Temporal validator: detects version regression | Given existing release_id "2024.05" and incoming "2023.05", returns failure | FR-3.6 | P6-04 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-10 | UNIT | Temporal validator: passes on monotonic version | Given existing "2023.05" and incoming "2024.05", returns success | FR-3.6 | P6-04 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-11 | UNIT | Append-only validator: detects mutation of prior-release rows | Given a fact table where a prior-release row's wage value changed, returns failure identifying the mutated row | FR-3.7 | P6-05 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-12 | UNIT | Schema drift detector: reports added, removed, and retyped columns between two schema snapshots | Given schemas A and B differing by one added and one removed column, detector lists both changes | FR-3.8 | P6-06 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-13 | UNIT | Row-count shift detector: reports percentage and absolute change | Given prior count 1000 and current count 1250, reports +250 / +25% | FR-3.9 | P6-07 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-14 | UNIT | Measure delta detector: identifies top N measures with largest relative change | Given two sets of mean_annual_wage by occupation, returns top 5 by percentage change | FR-3.9 | P6-07 | 2026-03-23 13:48 | 2026-03-23 13:50 |

### Failure Classification & Gating Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T6-15 | UNIT | Failure classification enum contains all required values | Enum includes: download_failure, source_format_failure, schema_drift_failure, validation_failure, load_failure, publish_blocked | FR-3.10, FR-6.4 | P6-08 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-16 | INTEGRATION | Publication gate blocks mart refresh when any validation fails | Trigger a grain validation failure → warehouse_publish returns publish_blocked; marts are not refreshed | FR-3.10, FR-5.6 | P6-09 | 2026-03-23 13:48 | 2026-03-23 13:50 |

### Failure-Mode Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T6-17 | FAILURE | Schema drift: pipeline fails fast at staging, classifies as schema_drift_failure, preserves raw, blocks publication | Given an OEWS file with a renamed column: staging fails, run_manifest shows schema_drift_failure, raw file retained, no mart refresh | FM-1 | P6-10 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-18 | FAILURE | Partial/corrupted source: pipeline retains raw, marks run incomplete, blocks downstream | Given a truncated download: raw file stored, run_manifest shows load_failure with incomplete flag, no warehouse load attempted | FM-6 | P6-11 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-19 | FAILURE | Material delta: pipeline emits delta report instead of silent acceptance | Given an OEWS release where total national employment shifts 30% vs. prior, pipeline emits delta report with occupation-level detail | FM-7 | P6-12 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-20 | FAILURE | Geography definition change: new definitions appended, old rows not mutated | Given a release where a state FIPS changed name, dim_geography gains new rows; prior geography_key fact associations unchanged | FM-3 | P6-09 | 2026-03-23 13:48 | 2026-03-23 13:50 |
| `[X]` | T6-21 | FAILURE | Suppressed OEWS values preserved as null | Given a row with BLS suppression markers, loaded fact has null wage fields, not zero or placeholder values | FM-4 | P6-09 | 2026-03-23 13:48 | 2026-03-23 13:50 |

---

## Phase 7 Tests: Observability & Run Reporting

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T7-01 | UNIT | Run manifest completion update populates all required fields | After pipeline completion, run_manifest record has non-null: row_count_raw, row_count_stage, row_count_loaded, load_status, failure_classification (or null on success), validation_summary | FR-6.3, FR-6.4 | P7-01 | 2026-03-23 13:54 | 2026-03-23 13:56 |
| `[X]` | T7-02 | UNIT | Row-count delta reporter computes correct delta against prior successful run | Given prior run with 1000 rows and current with 1050, reports +50 / +5.0% | FR-6.5 | P7-02 | 2026-03-23 13:54 | 2026-03-23 13:56 |
| `[X]` | T7-03 | UNIT | Row-count delta reporter handles first run (no prior) without error | Returns "no prior run" indicator, not an error | FR-6.5 | P7-02 | 2026-03-23 13:54 | 2026-03-23 13:56 |
| `[X]` | T7-04 | UNIT | Schema drift report emitter produces structured output listing all changes | Given a schema change, output includes dataset name, release pair, and list of added/removed/retyped columns | FR-6.6 | P7-03 | 2026-03-23 13:54 | 2026-03-23 13:56 |
| `[X]` | T7-05 | UNIT | Top measure delta reporter identifies correct top-N measures by change magnitude | Given wage data for 10 occupations across two releases, correctly ranks the top 5 by percentage change | FR-6.7 | P7-04 | 2026-03-23 13:54 | 2026-03-23 13:56 |
| `[X]` | T7-06 | UNIT | Reconciliation summary reporter compares loaded totals against published reference | Given loaded national total employment and published BLS total, reports match/mismatch with percentage difference | FR-6.8 | P7-05 | 2026-03-23 13:54 | 2026-03-23 13:56 |
| `[X]` | T7-07 | INTEGRATION | Run inspection view: querying a single run_id returns all metadata, row counts, validation results, and failure classification | Single query by run_id returns complete run picture without additional joins or code inspection | FR-6.9 | P7-06 | 2026-03-23 13:54 | 2026-03-23 13:56 |

---

## Phase 8 Tests: Orchestration

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T8-01 | INTEGRATION | `taxonomy_refresh` executes full sequence: extract → parse → validate → load SOC | dim_occupation and bridge_occupation_hierarchy populated; run_manifest record created and completed | OR-1 | P8-01 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-02 | INTEGRATION | `oews_refresh` executes full sequence: extract → parse → validate → load OEWS | fact_occupation_employment_wages populated; dim_geography populated; run_manifest completed | OR-1 | P8-02 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-03 | INTEGRATION | `onet_refresh` executes full sequence: extract → parse → validate → load O*NET | All 8 O*NET tables populated; run_manifest completed | OR-1 | P8-03 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-04 | INTEGRATION | `warehouse_publish` publishes marts only after all validations pass | All 5 marts populated; run_manifest shows success | OR-1, OR-4 | P8-04 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-05 | INTEGRATION | Dependency enforcement: `taxonomy_refresh` completes before `oews_refresh` begins on new SOC version | When new SOC version detected, oews_refresh waits for taxonomy_refresh completion; attempting to run oews_refresh first results in dependency block | OR-2, NFR-8 | P8-05 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-06 | INTEGRATION | Independent execution: `oews_refresh` and `onet_refresh` run concurrently without conflict | Both pipelines complete successfully when started simultaneously; no deadlocks or data corruption | OR-3, NFR-9 | P8-06 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-07 | INTEGRATION | Publish gating: `warehouse_publish` blocked when upstream validation fails | Introduce a grain violation in OEWS staging → warehouse_publish returns publish_blocked; no marts refreshed | OR-4, OR-7, FR-5.6 | P8-07 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-08 | IDEMPOTENT | Dataset-level idempotence: rerun any pipeline for same version produces no change | Row counts across all target tables unchanged after rerun of each pipeline | OR-5, FR-4.9 | P8-08, P8-12 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-09 | INTEGRATION | Run manifest lifecycle: created at pipeline start, updated at completion | Manifest record exists with created_at timestamp before pipeline work begins; updated with completion fields after pipeline ends | OR-6 | P8-09 | 2026-03-23 14:00 | 2026-03-23 14:04 |
| `[X]` | T8-10 | FAILURE | No-retry on semantic validation failure: pipeline stops, does not re-attempt | Trigger a referential integrity failure → pipeline records validation_failure and halts; no retry loop observed | NFR-7 | P8-10 | 2026-03-23 14:00 | 2026-03-23 14:04 |

---

## Phase 9 Tests: Analyst Marts

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[X]` | T9-01 | QUERY | `occupation_summary` grain is one row per occupation | Zero duplicates on occupation_key; every `dim_occupation` row with is_current=true appears | FR-5.1 | P9-01 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-02 | QUERY | `occupation_summary` includes hierarchy fields (major group, minor group, broad, detailed) | For SOC 15-1252, major_group = "15-0000", hierarchy fields non-null | FR-5.1 | P9-01 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-03 | QUERY | `occupation_wages_by_geography` grain is one row per occupation per geography | Zero duplicates on occupation_key + geography_key; contains employment_count, mean_annual_wage, median_annual_wage | FR-5.2 | P9-02 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-04 | QUERY | `occupation_wages_by_geography` joins resolve without fan-out or loss | Row count matches expected: (count of occupations in facts) × (count of geographies per occupation) | FR-5.2 | P9-02 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-05 | QUERY | `occupation_skill_profile` grain is one row per occupation per skill per scale type | Zero duplicates on occupation_key + skill_key + scale_type | FR-5.3 | P9-03 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-06 | QUERY | `occupation_skill_profile` uses current O*NET version only | All rows have source_version matching the latest loaded O*NET version | FR-5.3 | P9-03 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-07 | QUERY | `occupation_task_profile` grain is one row per occupation per task | Zero duplicates on occupation_key + task_key | FR-5.4 | P9-04 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-08 | QUERY | `occupation_similarity_seeded` produces non-trivial similarity scores | For Software Developers (15-1252), at least 5 similar occupations returned with similarity > 0 | FR-5.5 | P9-05 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-09 | QUERY | All marts trace back to source lineage | Every mart row can be joined back to a source_release_id via warehouse keys | FR-4.11 | P9-01 through P9-05 | 2026-03-23 14:10 | 2026-03-23 14:12 |
| `[X]` | T9-10 | INTEGRATION | Publish gating: marts not refreshed when upstream validation is in failed state | With a pending validation failure, mart tables retain prior content; no partial refresh | FR-5.6, OR-7 | P9-06 | 2026-03-23 14:10 | 2026-03-23 14:12 |

---

## Phase 10 Tests: Employment Projections (Optional R1)

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | T10-01 | UNIT | Projections parser extracts projection cycle, base year, target year, occupation code, employment values | Parsed rows match expected values for at least 3 known occupations | FR-2.4 | P10-03 | | |
| `[ ]` | T10-02 | CONTRACT | `stage__bls__employment_projections` has all required columns with correct types | Table exists with expected schema | FR-2.9 | P10-04 | | |
| `[ ]` | T10-03 | GRAIN | `stage__bls__employment_projections` has no duplicate rows at declared grain | Zero duplicates on projection_cycle + occupation_code + source_release_id | FR-3.2 | P10-08 | | |
| `[ ]` | T10-04 | GRAIN | `fact_occupation_projections` has no duplicate rows (projection_cycle + occupation_key) | Zero duplicates on business key | FR-3.2 | P10-06 | | |
| `[ ]` | T10-05 | CONTRACT | `fact_occupation_projections` contains all required fields from data model | Table has: projection_cycle, occupation_key, base_year, projection_year, employment_base, employment_projected, employment_change_pct, source_release_id | FR-4.8 | P10-06 | | |
| `[ ]` | T10-06 | REF | Every occupation_key in projections fact references valid `dim_occupation` | Zero orphans | FR-3.3 | P10-08 | | |
| `[ ]` | T10-07 | IDEMPOTENT | Rerun projections load for same cycle: no duplicate fact rows | Row count unchanged after rerun | FR-4.9 | P10-07 | | |
| `[ ]` | T10-08 | INTEGRATION | `projections_refresh` pipeline executes full sequence without error | Fact table populated; run_manifest completed with success | OR-1 | P10-09 | | |

---

## Phase 11 Tests: End-to-End Integration & Portfolio

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | T11-01 | INTEGRATION | Full pipeline for Software Developers (15-1252): extract all sources → parse → validate → load → publish marts | All warehouse tables populated; all marts queryable; run_manifests for all pipelines show success | Design §18 | P11-01 | | |
| `[ ]` | T11-02 | REGRESSION | OEWS national total employment for "All Occupations" matches published BLS total within ±0.1% | Loaded employment_count for SOC 00-0000 national matches published value | — | P11-07 | | |
| `[ ]` | T11-03 | REGRESSION | OEWS mean annual wage for Software Developers national matches published value within ±$100 | Loaded mean_annual_wage for 15-1252 national matches published BLS figure | — | P11-07 | | |
| `[ ]` | T11-04 | REGRESSION | dim_occupation row count matches known SOC occupation count | Loaded occupation count for current SOC version matches published total (e.g., 867 for 2018 SOC) | — | P11-07 | | |
| `[ ]` | T11-05 | QUERY | Analyst query: state-level wage distribution for Software Developers returns all 50 states + DC + territories | Query returns ≥ 50 rows; each has non-null geography name, mean_annual_wage or explicit null for suppressed states | Design §18 | P11-05 | | |
| `[ ]` | T11-06 | QUERY | Analyst query: core skills for Software Developers returns skill names with scores | Query returns ≥ 10 skill rows for 15-1252; each has skill_name and data_value > 0 | Design §18 | P11-06 | | |
| `[ ]` | T11-07 | QUERY | Analyst query: core tasks for Software Developers returns task descriptions | Query returns ≥ 5 task rows for 15-1252; each has non-null task description | Design §18 | P11-06 | | |
| `[ ]` | T11-08 | IDEMPOTENT | Full pipeline re-execution: no duplicates anywhere | Row counts across all staging, dimension, fact, bridge, and mart tables are identical before and after rerun | FR-4.9 | P11-08 | | |
| `[ ]` | T11-09 | INTEGRATION | All deliverables DL-1 through DL-8 are present and verifiable | Each deliverable exists as a file or queryable artifact; reviewer can trace from raw source to mart output | DL-1 through DL-8 | P11-11 | | |

---

## Test Summary

| Phase | Description | Test Count |
|-------|-------------|------------|
| 1 | Project Foundation | 5 |
| 2 | Extraction Framework & Run Manifest | 16 |
| 3 | SOC Taxonomy Pipeline | 18 |
| 4 | OEWS Employment & Wages Pipeline | 31 |
| 5 | O*NET Semantic Pipeline | 32 |
| 6 | Validation Framework & Failure Handling | 21 |
| 7 | Observability & Run Reporting | 7 |
| 8 | Orchestration | 10 |
| 9 | Analyst Marts | 10 |
| 10 | Employment Projections (Optional R1) | 8 |
| 11 | End-to-End Integration & Portfolio | 9 |
| **Total** | | **167** |

### Tests by Type

| Type | Count | Purpose |
|------|-------|---------|
| UNIT | 46 | Isolated module correctness |
| CONTRACT | 14 | Schema stability enforcement |
| GRAIN | 20 | Business key uniqueness |
| REF | 10 | Foreign key integrity |
| SEMANTIC | 12 | Logical data correctness |
| TEMPORAL | 2 | Version ordering and immutability |
| DRIFT | 4 | Cross-release change detection |
| IDEMPOTENT | 8 | Rerun safety |
| FAILURE | 6 | Correct behavior under error conditions |
| INTEGRATION | 13 | Multi-module flow verification |
| QUERY | 8 | Mart output correctness |
| REGRESSION | 3 | Match against known published values |
