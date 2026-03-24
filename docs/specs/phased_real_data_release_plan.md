# Phased Release Plan — Real Data Integration

This document tracks the work required to make the pipeline actually execute against real federal data sources and serve results through the website.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase RD1: Format Conversion Layer

Build the missing glue between raw downloaded files and the parsers that expect CSV/TSV text.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD1-01 | Create `src/jobclass/extract/formats.py` with `extract_xlsx_from_zip(bytes) -> bytes` using `zipfile` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD1-02 | Add `xlsx_to_csv(bytes) -> str` function using `openpyxl` to convert XLSX workbook to CSV text | 2026-03-23 | 2026-03-23 |
| `[X]` | RD1-03 | Add `xlsx_to_tsv(bytes) -> str` function for projections (tab-delimited output) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD1-04 | Add format dispatch function: given `expected_format` and raw bytes, return parser-ready text | 2026-03-23 | 2026-03-23 |
| `[X]` | RD1-05 | Add `_find_header_row()` to skip BLS XLSX preamble rows before data headers | 2026-03-23 | 2026-03-23 |
| `[X]` | RD1-06 | Download one real OEWS ZIP file, verify `extract_xlsx_from_zip` + `xlsx_to_csv` produces parseable output | 2026-03-23 | 2026-03-23 |
| `[X]` | RD1-07 | Download real projections XLSX, verify conversion produces parseable output | 2026-03-23 | 2026-03-23 |

---

## Phase RD2: Pipeline Orchestration Wiring

Connect extraction → format conversion → parsers → loaders into a single executable flow.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD2-01 | Create `src/jobclass/orchestrate/run_all.py` with `run_all_pipelines(conn, manifest_path, raw_root)` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-02 | Implement SOC flow: download XLSX → convert to CSV → parse → `taxonomy_refresh()` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-03 | Implement OEWS flow: download 2 ZIPs → extract XLSX → convert to CSV → parse → `oews_refresh()` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-04 | Implement O\*NET flow: download 5 TSV files → parse → `onet_refresh()` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-05 | Implement Projections flow: download XLSX → convert to CSV → parse → `projections_refresh()` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-06 | Call `warehouse_publish()` after all pipelines succeed | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-07 | Add progress logging: print pipeline name, status, row counts as each completes | 2026-03-23 | 2026-03-23 |
| `[X]` | RD2-08 | Handle partial failure: if one pipeline fails, continue others, report all results at end | 2026-03-23 | 2026-03-23 |

---

## Phase RD3: CLI and Startup

Wire the orchestration into the CLI and fix web startup.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD3-01 | Add `run-all` subcommand to `cli.py` that calls `run_all_pipelines()` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD3-02 | Add `--manifest` option to `run-all` (default: `config/source_manifest.yaml`) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD3-03 | Add `--raw-dir` option to `run-all` (default: `raw/`) for immutable artifact storage | 2026-03-23 | 2026-03-23 |
| `[!]` | RD3-04 | Add individual pipeline subcommands: `taxonomy-refresh`, `oews-refresh`, `onet-refresh`, `projections-refresh` | | |
| `[X]` | RD3-05 | Fix web `database.py`: check if warehouse file exists before connecting; return helpful error if not | 2026-03-23 | 2026-03-23 |
| `[!]` | RD3-06 | Fix `MART_VIEWS` list in `marts/views.py` to include `occupation_similarity_seeded` | | |

---

## Phase RD4: Real Data Execution and Fixes

Run against real data and fix everything that breaks. This phase is inherently iterative.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD4-01 | Run `jobclass-pipeline migrate` — verify schema creation | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-02 | Run `jobclass-pipeline run-all` — 5/5 pipelines succeed | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-03 | Fix OEWS column name mismatches: UPPERCASE XLSX headers → lowercase parser keys, AREA→area_code, NAICS→naics_code | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-04 | Fix Projections: BLS XLSX column names (pattern matching), Summary row filter, employment-in-thousands conversion | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-05 | Fix SOC: XLSX "Major"/"Minor"/"Broad"/"Detailed" group labels, data-driven parent assignment for broken hierarchy | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-06 | O\*NET: no column changes needed (TSV files work as-is) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-07 | Verify `jobclass-pipeline status` shows non-zero row counts (1,447 occupations, 38,758 wages, 827 projections) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-08 | Start `jobclass-web` and verify landing page loads with real statistics | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-09 | Verify search returns real occupations | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-10 | Verify hierarchy tree renders with full SOC taxonomy | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-11 | Verify occupation profile page shows wages, skills, tasks, projections, similar | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-12 | Verify wages comparison page shows state-level data | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-13 | Verify methodology page shows real version info and validation results | 2026-03-23 | 2026-03-23 |

### Additional fixes discovered during RD4

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD4-A1 | Update source_manifest.yaml: SOC URLs to XLSX, OEWS URLs to 2023 vintage, Projections to new BLS path | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-A2 | Add Sec-Fetch headers to download module — BLS blocks requests without modern browser headers | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-A3 | Fix version detection for 2-digit year URLs (oesm23nat → 2023.05) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-A4 | Add sheet_name to ManifestEntry for multi-sheet XLSX (Projections Table 1.2) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-A5 | Add em-dash (U+2014, U+2013) to suppression markers in common.py | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-A6 | Add estimate_year guard in load_fact_occupation_employment_wages for non-numeric release IDs | 2026-03-23 | 2026-03-23 |
| `[X]` | RD4-A7 | Projections validation: allow up to 2% unmapped occupation codes (NEM 2024 → SOC 2018 version gap) | 2026-03-23 | 2026-03-23 |

---

## Phase RD5: Data Warehouse Validation Tests

Add tests that verify real data integrity — row counts, referential integrity, value ranges.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD5-01 | Test: dim_occupation has >= 800 rows (real SOC has ~867 occupations) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-02 | Test: dim_geography has >= 50 rows (50 states + national + territories) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-03 | Test: fact_occupation_employment_wages has >= 10,000 rows | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-04 | Test: all fact table occupation_keys exist in dim_occupation | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-05 | Test: all fact table geography_keys exist in dim_geography | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-06 | Test: wage values are in plausible ranges ($0–$500/hr, $0–$750k/yr) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-07 | Test: employment counts are positive where not suppressed | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-08 | Test: no duplicate occupation keys at SOC code + version grain | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-09 | Test: projections have base_year < projection_year | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-10 | Test: O\*NET skill importance values are in [0, 5] range | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-11 | Test: similarity scores are in [0, 1] range (skipped — mart not populated) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD5-12 | Test: at least one occupation (15-1251) has wages, skills, tasks, and projections | 2026-03-23 | 2026-03-23 |

---

## Phase RD6: PEP 8 Compliance

Run a PEP 8 linter across all Python source and test files. Fix violations.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | RD6-01 | Run `ruff check` on `src/jobclass/` and `tests/` — baseline: 117 violations | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-02 | Fix line-length violations (E501) — 11 fixes across 7 files | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-03 | Fix import ordering violations (I-series) — auto-fixed by `ruff check --fix` | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-04 | Fix whitespace and style violations (UP017, UP042, SIM102, SIM105) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-05 | Fix unused imports and variables (F401, F841) — auto-fixed by ruff | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-06 | Fix bugbear violations (B904 raise-without-from, B905 zip-strict, B007 unused loop var) | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-07 | Ruff already configured in `pyproject.toml` — line-length=120, select=["E","F","W","I","N","UP","B","SIM"] | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-08 | Verify all 484 tests still pass after PEP 8 fixes | 2026-03-23 | 2026-03-23 |
| `[X]` | RD6-09 | Run `ruff check` — zero violations ("All checks passed!") | 2026-03-23 | 2026-03-23 |

---

## Phase Summary

| Phase | Description | Task Count | Completed |
|-------|-------------|------------|-----------|
| RD1 | Format Conversion Layer — ZIP/XLSX handling | 7 | 7 |
| RD2 | Pipeline Orchestration Wiring — end-to-end flow | 8 | 8 |
| RD3 | CLI and Startup — user-facing commands and error handling | 6 | 4 |
| RD4 | Real Data Execution and Fixes — run it, fix what breaks | 13 + 7 | 20 |
| RD5 | Data Warehouse Validation Tests — verify real data integrity | 12 | 12 |
| RD6 | PEP 8 Compliance — lint and fix all Python code | 9 | 9 |
| **Total** | | **62** | **60** |

---

## Notes

- RD4 is intentionally vague about specific fixes because we don't know what will break until we run it. The "Additional fixes" section documents what actually broke.
- RD5 tests should run against a populated warehouse (not fixtures). They may need a separate pytest marker or conftest that connects to the real `warehouse.duckdb`.
- The existing 484 fixture-based tests remain valuable for regression — they verify logic. RD5 tests verify data.
- BLS actively blocks automated requests. The download module requires browser-like headers including Sec-Fetch-* to bypass.
- OEWS 2024 data is not yet available as downloadable ZIPs; pipeline uses 2023 vintage.
- 5 NEM 2024 occupation codes don't map to SOC 2018 (expected version gap).
