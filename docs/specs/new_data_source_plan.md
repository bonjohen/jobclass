# Phased Release Plan — New Data Source Integration

This document tracks the work required to integrate seven new data sources into the JobClass warehouse, following the requirements in `new_data_source_design.md`.

**Code review integration:** This plan incorporates relevant findings from `phased_code_review_release_plan_v2.md`. Code review tasks are prefixed with `CR2-` and placed in the NDS phase where they are most practical to implement. Remaining code review tasks not merged here are tracked in the CR2 plan and will be executed after all NDS phases.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase NDS0: Code Quality Prep (CR2 items)

Before adding new API endpoints and JS sections, clean up duplicated utilities and centralize registries. This prevents the new code from inheriting existing duplication.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CR2-01a | Add `fetchWithTimeout(url, timeoutMs)` and `FETCH_TIMEOUT_MS = 10000` to `main.js` | | |
| `[X]` | CR2-01b | Remove local `fetchWithTimeout` + `FETCH_TIMEOUT_MS` from all 10 JS files (geography_comparison, hierarchy, landing, methodology, occupation, occupation_comparison, ranked_movers, trend_explorer, trends, wages) | | |
| `[X]` | CR2-01c | Refactor `search.js` to use shared `fetchWithTimeout`; fix AbortController reuse (CR2-06) | | |
| `[X]` | CR2-01d | Update cache-busting version in `base.html` (`?v=NDS0`) | | |
| `[X]` | CR2-02a | Create `src/jobclass/web/lessons.py` with canonical `LESSONS` registry | | |
| `[X]` | CR2-02b | Update `app.py`, `test_lessons.py`, `build_static.py` to import from `lessons.py` | | |
| `[X]` | CR2-02c | Add test: verify every registry entry has a corresponding template file | | |
| `[X]` | CR2-04a | Fix `_table_exists()` in `trends.py`: catch `CatalogException` instead of bare `Exception`; add identifier validation | | |
| `[X]` | CR2-09a | Move drift threshold magic numbers in `validate/framework.py` to named constants with rationale comments | | |
| `[X]` | CR2-18a | Remove redundant `try/except` around `shutil.rmtree(..., ignore_errors=True)` in `deploy_pages.py` | | |
| `[X]` | CR2-17a | Add pre-push sanity checks to `deploy_pages.py`: verify `_site/index.html`, `_site/static/`, `_site/api/` exist | | |
| `[X]` | NDS0-01 | Run all tests — verify no regressions from prep work | | |

---

## Phase NDS1: Surface O\*NET Knowledge (DS-01)

Expose the already-loaded O\*NET knowledge data through the API and website.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS1-01 | Add `/api/occupations/{soc_code}/knowledge` endpoint in `occupations.py`: query `bridge_occupation_knowledge` joined to `dim_knowledge`, filter `scale_id = 'IM'`, return element name + importance + level, ordered by importance desc | | |
| `[X]` | NDS1-02 | Add `loadKnowledge()` function in `occupation.js`: fetch knowledge endpoint, render table with Knowledge Domain / Importance / Level columns, hide section if empty | | |
| `[X]` | NDS1-03 | Add "Knowledge" section div to `occupation.html` template (hidden by default, same pattern as skills/tasks) | | |
| `[X]` | NDS1-04 | Add knowledge endpoint to per-occupation JSON generation in `build_static.py` | | |
| `[X]` | NDS1-05 | Add test: knowledge endpoint returns 200 with expected fields for a known occupation | | |
| `[X]` | NDS1-06 | Add test: occupation profile page contains knowledge section markup | | |
| `[X]` | NDS1-07 | Verify on live server: knowledge section renders correctly for an occupation with knowledge data (e.g., 15-1252) | | |

**Code review (CR2-03):** Add Pydantic response models for trends API alongside the new knowledge endpoint, since we are already modifying `models.py`.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | CR2-03a | Define `TrendSeriesResponse`, `TrendCompareResponse`, `TrendGeographyResponse`, `TrendMoversResponse` in `models.py` | | |
| `[ ]` | CR2-03b | Apply `response_model=` to all 7 endpoints in `trends.py` | | |
| `[ ]` | CR2-03c | Run all trends tests — verify responses conform to models | | |

---

## Phase NDS2: Surface O\*NET Abilities (DS-02)

Expose the already-loaded O\*NET abilities data through the API and website.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS2-01 | Add `/api/occupations/{soc_code}/abilities` endpoint in `occupations.py`: same pattern as knowledge, using `bridge_occupation_ability` and `dim_ability` | | |
| `[X]` | NDS2-02 | Add `loadAbilities()` function in `occupation.js`: fetch abilities endpoint, render table, hide section if empty | | |
| `[X]` | NDS2-03 | Add "Abilities" section div to `occupation.html` template | | |
| `[X]` | NDS2-04 | Add abilities endpoint to per-occupation JSON generation in `build_static.py` | | |
| `[X]` | NDS2-05 | Add test: abilities endpoint returns 200 with expected fields | | |
| `[X]` | NDS2-06 | Add test: occupation profile page contains abilities section markup | | |
| `[X]` | NDS2-07 | Verify on live server: abilities section renders correctly | | |

**Code review (CR2-08):** Add CSS section comments while adding new profile section styles.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | CR2-08a | Add section comment headers to `main.css` for each major section (variables, layout, nav, cards, search, hierarchy, trends, occupation, wages, lessons, responsive) | | |
| `[ ]` | CR2-08b | Audit repeated magic numbers (border-radius, spacing) — replace 3+ occurrences with CSS variables | | |

---

## Phase NDS3: O\*NET Work Activities (DS-03)

Add a new O\*NET domain for generalized work activities.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS3-01 | Create migration SQL: `dim_work_activity` table (work_activity_key, element_id, element_name, source_version), sequence `seq_work_activity_key`, unique index on (element_id, source_version) | | |
| `[X]` | NDS3-02 | Create migration SQL: `bridge_occupation_work_activity` table (occupation_key, work_activity_key, scale_id, data_value, n, source_version, source_release_id, load_timestamp), staging table `stage__onet__work_activities` | | |
| `[X]` | NDS3-03 | Add manifest entry for `onet_work_activities` in `source_manifest.yaml` pointing to `Work%20Activities.txt` | | |
| `[X]` | NDS3-04 | Add `onet_work_activities_parser` alias in `onet.py` using existing `parse_onet_descriptors()` (the file format is identical to Skills) | | |
| `[X]` | NDS3-05 | Add loader functions: `load_dim_work_activity()` and `load_bridge_occupation_work_activity()` in `onet.py`, following the skill loader pattern | | |
| `[X]` | NDS3-06 | Wire work activities into `onet_refresh()` pipeline in `pipelines.py` | | |
| `[X]` | NDS3-07 | Add `/api/occupations/{soc_code}/activities` endpoint | | |
| `[X]` | NDS3-08 | Add `loadActivities()` function in `occupation.js` and "Work Activities" section in `occupation.html` | | |
| `[X]` | NDS3-09 | Add activities endpoint to `build_static.py` per-occupation JSON generation | | |
| `[X]` | NDS3-10 | Add unit tests: parser returns expected rows from sample TSV, loader is idempotent | | |
| `[X]` | NDS3-11 | Add web tests: endpoint returns 200, profile page has activities section | | |
| `[ ]` | NDS3-12 | Run `jobclass-pipeline run-all` and verify work activities load with real data | | |

**Code review (CR2-05):** Fix shim error handling while adding new endpoints to `build_static.py`.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CR2-05a | In STATIC_SHIM occupation comparison handler, filter null results from assembled occupations array | | |
| `[X]` | CR2-05b | Add `console.warn()` in shim catch blocks for failed occupation fetches | | |
| `[X]` | CR2-05c | In `occupation_comparison.js`, add null-check before iterating occupation series data | | |

---

## Phase NDS4: O\*NET Education & Training (DS-04)

Add education and training requirements with category distributions.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS4-01 | Create migration SQL: `dim_education_requirement` table (education_key, element_id, element_name, category, category_label, source_version), sequence, unique index on (element_id, category, source_version) | | |
| `[X]` | NDS4-02 | Create migration SQL: `bridge_occupation_education` table, staging table `stage__onet__education` | | |
| `[X]` | NDS4-03 | Add manifest entry for `onet_education` in `source_manifest.yaml` pointing to `Education%2C%20Training%2C%20and%20Experience.txt` | | |
| `[X]` | NDS4-04 | Create `parse_onet_education()` parser in `onet.py`: handle the `Category` column not present in other O\*NET files, return dataclass with category + percentage data_value | | |
| `[X]` | NDS4-05 | Create `OnetEducationRow` dataclass with fields: occupation_code, element_id, element_name, scale_id, category, data_value, n, source_release_id, parser_version | | |
| `[X]` | NDS4-06 | Add loader functions: `load_dim_education_requirement()` (extract distinct element_id + category combinations) and `load_bridge_occupation_education()` | | |
| `[X]` | NDS4-07 | Wire education into `onet_refresh()` pipeline | | |
| `[X]` | NDS4-08 | Add `/api/occupations/{soc_code}/education` endpoint: return category distributions per education element, include a `summary` field with the dominant education level | | |
| `[X]` | NDS4-09 | Add `loadEducation()` function in `occupation.js`: render summary (e.g., "Typical: Bachelor's degree") with expandable detail table showing percentage breakdown | | |
| `[X]` | NDS4-10 | Add "Education & Training" section in `occupation.html` | | |
| `[X]` | NDS4-11 | Add education endpoint to `build_static.py` per-occupation JSON generation | | |
| `[X]` | NDS4-12 | Add unit tests: parser handles Category column, loader deduplicates correctly | | |
| `[X]` | NDS4-13 | Add web tests: endpoint returns 200 with distribution data, profile page has education section | | |
| `[ ]` | NDS4-14 | Run pipeline and verify education data loads with real data | | |

---

## Phase NDS5: O\*NET Technology Skills (DS-05)

Add tools and technology used by occupation.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS5-01 | Create migration SQL: `dim_technology` table (technology_key, commodity_code, commodity_title, t2_type, example_name, source_version), sequence, unique index on (commodity_code, example_name, source_version) | | |
| `[X]` | NDS5-02 | Create migration SQL: `bridge_occupation_technology` table (no scale_id or data_value — binary association), staging table `stage__onet__technology_skills` | | |
| `[X]` | NDS5-03 | Add manifest entry for `onet_technology_skills` in `source_manifest.yaml` pointing to `Technology%20Skills.txt` | | |
| `[X]` | NDS5-04 | Create `parse_onet_technology()` parser in `onet.py`: handle the different column structure (T2 Type, T2 Example, Commodity Code, Commodity Title — no Scale ID, Data Value, N) | | |
| `[X]` | NDS5-05 | Create `OnetTechnologyRow` dataclass with fields: occupation_code, t2_type, example_name, commodity_code, commodity_title, source_release_id, parser_version | | |
| `[X]` | NDS5-06 | Add loader functions: `load_dim_technology()` and `load_bridge_occupation_technology()` | | |
| `[X]` | NDS5-07 | Wire technology skills into `onet_refresh()` pipeline | | |
| `[X]` | NDS5-08 | Add `/api/occupations/{soc_code}/technology` endpoint: return tools grouped by `t2_type` (Tools vs Technology) | | |
| `[X]` | NDS5-09 | Add `loadTechnology()` function in `occupation.js`: render as grouped list (Tools heading + list, Technology heading + list) | | |
| `[X]` | NDS5-10 | Add "Tools & Technology" section in `occupation.html` | | |
| `[X]` | NDS5-11 | Add technology endpoint to `build_static.py` per-occupation JSON generation | | |
| `[X]` | NDS5-12 | Add unit tests: parser handles Technology Skills column structure, loader deduplicates | | |
| `[X]` | NDS5-13 | Add web tests: endpoint returns 200 with grouped data, profile page has technology section | | |
| `[ ]` | NDS5-14 | Run pipeline and verify technology data loads with real data | | |

---

## Phase NDS6: BLS CPI-U Inflation Adjustment (DS-06)

Add CPI data and real (inflation-adjusted) wage metrics.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS6-01 | Create migration SQL: `dim_price_index` table (price_index_key, series_id, series_name, base_period, seasonally_adjusted, source_release_id), sequence | | |
| `[X]` | NDS6-02 | Create migration SQL: `fact_price_index_observation` table (observation_key, price_index_key, period_key FK, index_value, source_release_id, run_id), unique index on (price_index_key, period_key) | | |
| `[X]` | NDS6-03 | Add manifest entry for `bls_cpi` in `source_manifest.yaml` pointing to `https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems` | | |
| `[X]` | NDS6-04 | Create `src/jobclass/parse/cpi.py` with `parse_cpi()`: filter to series `CUSR0000SA0`, period `M13` (annual average), extract year + value. Handle whitespace-padded columns | | |
| `[X]` | NDS6-05 | Create `CpiRow` dataclass with fields: series_id, year, period, value, source_release_id, parser_version | | |
| `[X]` | NDS6-06 | Create staging table `stage__bls__cpi` and staging loader | | |
| `[X]` | NDS6-07 | Create `src/jobclass/load/cpi.py` with `load_dim_price_index()` and `load_fact_price_index_observation()` | | |
| `[X]` | NDS6-08 | Create `cpi_refresh()` pipeline function in `pipelines.py` and wire into `run_all.py` (runs after OEWS, before timeseries_refresh) | | |
| `[X]` | NDS6-09 | Register `real_mean_annual_wage` and `real_median_annual_wage` in `dim_metric` with `derivation_type = 'derived'`, `units = 'dollars'`, `display_format = '$#,##0'` | | |
| `[X]` | NDS6-10 | Add `compute_real_wages()` derivation step in `timeseries_refresh.py`: join nominal wage observations to CPI observations on period_key, apply deflation formula `nominal × (CPI_base / CPI_year)`, insert into `fact_derived_series` | | |
| `[X]` | NDS6-11 | Choose and document the base year for deflation (e.g., 2023 = latest year with data). Store base year in a config constant | | |
| `[X]` | NDS6-12 | Add "Real Mean Annual Wage" and "Real Median Annual Wage" options to metric dropdowns in Trend Explorer and Ranked Movers HTML templates | | |
| `[X]` | NDS6-13 | Add per-metric trend files for real wages to `build_static.py` per-occupation generation | | |
| `[X]` | NDS6-14 | Add unit tests: CPI parser extracts correct year + value from sample data, handles whitespace padding | | |
| `[X]` | NDS6-15 | Add unit tests: deflation formula produces known values (e.g., $100,000 in 2021 → expected 2023 dollars) | | |
| `[X]` | NDS6-16 | Add web tests: real wage metrics appear in trend API response, trend explorer page has real wage options | | |
| `[ ]` | NDS6-17 | Run pipeline and verify: CPI loads, real wages computed, trend explorer shows real wage series for a known occupation | | |

---

## Phase NDS7: SOC 2010↔2018 Crosswalk (DS-07)

Add the crosswalk and extend comparable history with pre-2018 OEWS vintages.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS7-01 | Create migration SQL: `bridge_soc_crosswalk` table (crosswalk_key, source_soc_code, source_soc_version, target_soc_code, target_soc_version, mapping_type, source_release_id), unique index on (source_soc_code, source_soc_version, target_soc_code, target_soc_version) | | |
| `[X]` | NDS7-02 | Add manifest entry for `soc_crosswalk` in `source_manifest.yaml` pointing to `https://www.bls.gov/soc/2018/soc_2018_crosswalk.xlsx` | | |
| `[X]` | NDS7-03 | Create `parse_soc_crosswalk()` in `soc.py`: read XLSX, extract 2010↔2018 code pairs, classify mapping type (1:1, split, merge, complex) by computing cardinality of each source and target code | | |
| `[X]` | NDS7-04 | Create `CrosswalkRow` dataclass with fields: source_soc_code, source_soc_version, target_soc_code, target_soc_version, mapping_type, source_release_id, parser_version | | |
| `[X]` | NDS7-05 | Create loader `load_bridge_soc_crosswalk()` in `src/jobclass/load/soc.py` with idempotent delete-before-insert | | |
| `[ ]` | NDS7-06 | Load SOC 2010 occupations into `dim_occupation` with `soc_version = '2010'`, `is_current = false`. Source: crosswalk file contains 2010 titles | | |
| `[ ]` | NDS7-07 | Add OEWS 2017 national + state manifest entries (first pre-2018 vintage to integrate) | | |
| `[ ]` | NDS7-08 | Verify OEWS 2017 parser handles column variations (check `_OEWS_COLUMN_ALIASES` in `oews.py`) | | |
| `[ ]` | NDS7-09 | Run OEWS 2017 extraction and verify staging tables contain rows tagged with 2017 source_release_id | | |
| `[ ]` | NDS7-10 | Modify `build_comparable_history()` in `timeseries_refresh.py`: for 1:1 crosswalk mappings, create comparable-history observations that remap SOC 2010 occupation_keys to SOC 2018 occupation_keys | | |
| `[ ]` | NDS7-11 | For split/merge mappings with employment_count: sum component values when building comparable-history rows. Tag with `mapping_type = 'aggregated'` | | |
| `[ ]` | NDS7-12 | For split/merge mappings with wage metrics: only include 1:1 mappings. Wage averages cannot be meaningfully combined without employment weights in the initial release | | |
| `[ ]` | NDS7-13 | Add OEWS 2012–2016 national + state manifest entries (10 additional entries) | | |
| `[ ]` | NDS7-14 | Run full pipeline with all OEWS vintages 2012–2023 and verify time-series extends back to 2012 for 1:1 mapped occupations | | |
| `[X]` | NDS7-15 | Add unit tests: crosswalk parser classifies known mappings correctly (test 1:1, split, merge, complex examples) | | |
| `[ ]` | NDS7-16 | Add unit tests: comparable history builder remaps occupation keys through crosswalk | | |
| `[ ]` | NDS7-17 | Add warehouse tests: verify Trend Explorer shows 2012–2023 data for a 1:1 mapped occupation | | |
| `[ ]` | NDS7-18 | Add warehouse tests: verify split/merge occupations have employment comparable history but not wage comparable history | | |
| `[ ]` | NDS7-19 | Verify on live server: Trend Explorer for a known occupation (e.g., 15-1252 Software Developers) shows a longer time-series | | |

---

## Phase NDS8: Integration Testing & Deployment

Final verification across all new sources. Includes remaining code review test coverage items.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | NDS8-01 | Run `ruff check src/ tests/` and `ruff format --check src/ tests/` — all clean | | |
| `[X]` | NDS8-02 | Run `pytest tests/unit/ tests/web/ -q` — all tests pass (653 tests) | | |
| `[ ]` | NDS8-03 | Run `jobclass-pipeline run-all` with all new sources enabled — all stages succeed | | |
| `[ ]` | NDS8-04 | Run `pytest tests/warehouse/` against populated warehouse — all validation tests pass | | |
| `[ ]` | NDS8-05 | Verify occupation profile page for 15-1252 (Software Developers) shows: Skills, Knowledge, Abilities, Work Activities, Education, Tasks, Technology, Projections, Similar | | |
| `[ ]` | NDS8-06 | Verify occupation profile page for 11-1011 (Chief Executives) shows available sections and hides unavailable sections gracefully | | |
| `[ ]` | NDS8-07 | Verify Trend Explorer shows real wage metrics in dropdown and renders inflation-adjusted series | | |
| `[ ]` | NDS8-08 | Verify Trend Explorer for a 1:1 crosswalked occupation shows data back to 2012 | | |
| `[ ]` | NDS8-09 | Rebuild static site: `MSYS_NO_PATHCONV=1 python scripts/build_static.py --base-path /jobclass` | | |
| `[ ]` | NDS8-10 | Deploy static site: `python scripts/deploy_pages.py` | | |
| `[ ]` | NDS8-11 | Verify GitHub Pages site renders new profile sections and real wage trends correctly | | |
| `[ ]` | NDS8-12 | Update `CLAUDE.md` with new source descriptions, test counts, and any new CLI commands | | |

**Code review test coverage (CR2-10 through CR2-14):** Add static site build tests and close test coverage gaps for trends features.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | CR2-10a | Create `tests/test_build_static.py`: test shim injection, URL rewriting, per-year movers JSON, per-metric trend JSON, search index, lesson pages, `.nojekyll`, static assets copied | | |
| `[X]` | CR2-11a | Add tests for ranked movers year filter: explicit year, `available_years` field, nonexistent year, year+metric combo | | |
| `[X]` | CR2-12a | Add tests for trends comparison endpoints: >10 codes rejected, invalid SOC format, geography year/metric params, missing data graceful handling | | |
| `[ ]` | CR2-13a | Add CI step in `.github/workflows/ci.yml` that runs `python scripts/build_static.py --base-path /jobclass` and verifies `_site/index.html` exists | | |
| `[X]` | CR2-14a | Add contract tests: parse each trends endpoint response through Pydantic model, assert no validation errors | | |
| `[ ]` | CR2-16a | Expand Static Site section in CLAUDE.md with any new URL pattern → JSON file mappings added during NDS phases | | |

---

## Phase Summary

| Phase | Description | Task Count | CR2 Tasks | Status |
|-------|-------------|------------|-----------|--------|
| NDS0 | Code Quality Prep (CR2 items) | 12 | 12 | Not Started |
| NDS1 | Surface O\*NET Knowledge (DS-01) | 7 | +3 (CR2-03) | Not Started |
| NDS2 | Surface O\*NET Abilities (DS-02) | 7 | +2 (CR2-08) | Not Started |
| NDS3 | O\*NET Work Activities (DS-03) | 12 | +3 (CR2-05) | Not Started |
| NDS4 | O\*NET Education & Training (DS-04) | 14 | — | Not Started |
| NDS5 | O\*NET Technology Skills (DS-05) | 14 | — | Not Started |
| NDS6 | BLS CPI-U Inflation Adjustment (DS-06) | 17 | — | Not Started |
| NDS7 | SOC 2010↔2018 Crosswalk (DS-07) | 19 | — | Not Started |
| NDS8 | Integration Testing & Deployment | 12 | +6 (CR2-10–16) | Not Started |
| **Total** | | **114** | **26** | |

---

## Notes

- **NDS0 (Code Quality Prep) must be done first.** Extracting `fetchWithTimeout` to `main.js` and centralizing lesson slugs prevents new NDS code from inheriting existing duplication.
- **NDS1 and NDS2 have zero dependencies** and require no new downloads. They should be implemented first as quick wins.
- **NDS3 through NDS5 are independent** of each other. They all require O\*NET downloads but use separate files. They can be developed in parallel.
- **NDS6 (CPI) is independent** of all O\*NET work. It can start at any time.
- **NDS7 (Crosswalk) is the most complex phase** and has the highest risk. The crosswalk mapping classification and comparable-history extension involve non-trivial logic. Start after NDS1/NDS2 are validated.
- **NDS8 depends on all prior phases** completing. This is the final integration gate.
- **Incremental deployment is encouraged.** Each phase can be committed, pushed, and deployed independently. The static site should be rebuilt after each phase that adds new API endpoints.
- **OEWS vintage expansion (NDS7)** adds 12 new manifest entries (6 years × 2 files). This significantly increases pipeline run time. Consider adding a `--vintage` CLI flag to run specific vintages rather than all.
- **O\*NET version updates** (e.g., 29.1 → 30.0) may change file URLs. The manifest entries should use the version number in comments so they can be updated when a new O\*NET release drops.
- **Code review items not merged here** (CR2-15 cache-busting docs) are already addressed in the CLAUDE.md update.

## Code Review Cross-Reference

| CR2 Finding | Merged Into | Rationale |
|-------------|-------------|-----------|
| CR2-01 (fetchWithTimeout) | NDS0 | Must be done before adding new JS functions |
| CR2-02 (lesson slugs) | NDS0 | Must be done before any lesson changes |
| CR2-03 (trends Pydantic models) | NDS1 | Natural fit while modifying `models.py` for new endpoints |
| CR2-04 (_table_exists) | NDS0 | Quick fix, no dependencies |
| CR2-05 (shim error handling) | NDS3 | Natural fit while updating `build_static.py` |
| CR2-06 (search.js) | NDS0 | Merged with CR2-01 refactor |
| CR2-08 (CSS sections) | NDS2 | Natural fit while adding new profile section styles |
| CR2-09 (drift thresholds) | NDS0 | Quick fix, no dependencies |
| CR2-10 (static site tests) | NDS8 | Comprehensive testing phase |
| CR2-11 (movers year tests) | NDS8 | Testing phase |
| CR2-12 (comparison tests) | NDS8 | Testing phase |
| CR2-13 (CI static build) | NDS8 | Deployment phase |
| CR2-14 (contract tests) | NDS8 | Testing phase |
| CR2-16 (static site docs) | NDS8 | Final documentation update |
| CR2-17 (deploy sanity) | NDS0 | Quick fix, no dependencies |
| CR2-18 (redundant except) | NDS0 | Quick fix, no dependencies |
| CR2-15 (cache-bust docs) | Done | Already addressed in CLAUDE.md update |
