# Phased Release Plan — New Data Source Integration

This document tracks the work required to integrate seven new data sources into the JobClass warehouse, following the requirements in `new_data_source_design.md`.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase NDS1: Surface O\*NET Knowledge (DS-01)

Expose the already-loaded O\*NET knowledge data through the API and website.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS1-01 | Add `/api/occupations/{soc_code}/knowledge` endpoint in `occupations.py`: query `bridge_occupation_knowledge` joined to `dim_knowledge`, filter `scale_id = 'IM'`, return element name + importance + level, ordered by importance desc | | |
| `[ ]` | NDS1-02 | Add `loadKnowledge()` function in `occupation.js`: fetch knowledge endpoint, render table with Knowledge Domain / Importance / Level columns, hide section if empty | | |
| `[ ]` | NDS1-03 | Add "Knowledge" section div to `occupation.html` template (hidden by default, same pattern as skills/tasks) | | |
| `[ ]` | NDS1-04 | Add knowledge endpoint to per-occupation JSON generation in `build_static.py` | | |
| `[ ]` | NDS1-05 | Add test: knowledge endpoint returns 200 with expected fields for a known occupation | | |
| `[ ]` | NDS1-06 | Add test: occupation profile page contains knowledge section markup | | |
| `[ ]` | NDS1-07 | Verify on live server: knowledge section renders correctly for an occupation with knowledge data (e.g., 15-1252) | | |

---

## Phase NDS2: Surface O\*NET Abilities (DS-02)

Expose the already-loaded O\*NET abilities data through the API and website.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS2-01 | Add `/api/occupations/{soc_code}/abilities` endpoint in `occupations.py`: same pattern as knowledge, using `bridge_occupation_ability` and `dim_ability` | | |
| `[ ]` | NDS2-02 | Add `loadAbilities()` function in `occupation.js`: fetch abilities endpoint, render table, hide section if empty | | |
| `[ ]` | NDS2-03 | Add "Abilities" section div to `occupation.html` template | | |
| `[ ]` | NDS2-04 | Add abilities endpoint to per-occupation JSON generation in `build_static.py` | | |
| `[ ]` | NDS2-05 | Add test: abilities endpoint returns 200 with expected fields | | |
| `[ ]` | NDS2-06 | Add test: occupation profile page contains abilities section markup | | |
| `[ ]` | NDS2-07 | Verify on live server: abilities section renders correctly | | |

---

## Phase NDS3: O\*NET Work Activities (DS-03)

Add a new O\*NET domain for generalized work activities.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS3-01 | Create migration SQL: `dim_work_activity` table (work_activity_key, element_id, element_name, source_version), sequence `seq_work_activity_key`, unique index on (element_id, source_version) | | |
| `[ ]` | NDS3-02 | Create migration SQL: `bridge_occupation_work_activity` table (occupation_key, work_activity_key, scale_id, data_value, n, source_version, source_release_id, load_timestamp), staging table `stage__onet__work_activities` | | |
| `[ ]` | NDS3-03 | Add manifest entry for `onet_work_activities` in `source_manifest.yaml` pointing to `Work%20Activities.txt` | | |
| `[ ]` | NDS3-04 | Add `onet_work_activities_parser` alias in `onet.py` using existing `parse_onet_descriptors()` (the file format is identical to Skills) | | |
| `[ ]` | NDS3-05 | Add loader functions: `load_dim_work_activity()` and `load_bridge_occupation_work_activity()` in `onet.py`, following the skill loader pattern | | |
| `[ ]` | NDS3-06 | Wire work activities into `onet_refresh()` pipeline in `pipelines.py` | | |
| `[ ]` | NDS3-07 | Add `/api/occupations/{soc_code}/activities` endpoint | | |
| `[ ]` | NDS3-08 | Add `loadActivities()` function in `occupation.js` and "Work Activities" section in `occupation.html` | | |
| `[ ]` | NDS3-09 | Add activities endpoint to `build_static.py` per-occupation JSON generation | | |
| `[ ]` | NDS3-10 | Add unit tests: parser returns expected rows from sample TSV, loader is idempotent | | |
| `[ ]` | NDS3-11 | Add web tests: endpoint returns 200, profile page has activities section | | |
| `[ ]` | NDS3-12 | Run `jobclass-pipeline run-all` and verify work activities load with real data | | |

---

## Phase NDS4: O\*NET Education & Training (DS-04)

Add education and training requirements with category distributions.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS4-01 | Create migration SQL: `dim_education_requirement` table (education_key, element_id, element_name, category, category_label, source_version), sequence, unique index on (element_id, category, source_version) | | |
| `[ ]` | NDS4-02 | Create migration SQL: `bridge_occupation_education` table, staging table `stage__onet__education` | | |
| `[ ]` | NDS4-03 | Add manifest entry for `onet_education` in `source_manifest.yaml` pointing to `Education%2C%20Training%2C%20and%20Experience.txt` | | |
| `[ ]` | NDS4-04 | Create `parse_onet_education()` parser in `onet.py`: handle the `Category` column not present in other O\*NET files, return dataclass with category + percentage data_value | | |
| `[ ]` | NDS4-05 | Create `OnetEducationRow` dataclass with fields: occupation_code, element_id, element_name, scale_id, category, data_value, n, source_release_id, parser_version | | |
| `[ ]` | NDS4-06 | Add loader functions: `load_dim_education_requirement()` (extract distinct element_id + category combinations) and `load_bridge_occupation_education()` | | |
| `[ ]` | NDS4-07 | Wire education into `onet_refresh()` pipeline | | |
| `[ ]` | NDS4-08 | Add `/api/occupations/{soc_code}/education` endpoint: return category distributions per education element, include a `summary` field with the dominant education level | | |
| `[ ]` | NDS4-09 | Add `loadEducation()` function in `occupation.js`: render summary (e.g., "Typical: Bachelor's degree") with expandable detail table showing percentage breakdown | | |
| `[ ]` | NDS4-10 | Add "Education & Training" section in `occupation.html` | | |
| `[ ]` | NDS4-11 | Add education endpoint to `build_static.py` per-occupation JSON generation | | |
| `[ ]` | NDS4-12 | Add unit tests: parser handles Category column, loader deduplicates correctly | | |
| `[ ]` | NDS4-13 | Add web tests: endpoint returns 200 with distribution data, profile page has education section | | |
| `[ ]` | NDS4-14 | Run pipeline and verify education data loads with real data | | |

---

## Phase NDS5: O\*NET Technology Skills (DS-05)

Add tools and technology used by occupation.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS5-01 | Create migration SQL: `dim_technology` table (technology_key, commodity_code, commodity_title, t2_type, example_name, source_version), sequence, unique index on (commodity_code, example_name, source_version) | | |
| `[ ]` | NDS5-02 | Create migration SQL: `bridge_occupation_technology` table (no scale_id or data_value — binary association), staging table `stage__onet__technology_skills` | | |
| `[ ]` | NDS5-03 | Add manifest entry for `onet_technology_skills` in `source_manifest.yaml` pointing to `Technology%20Skills.txt` | | |
| `[ ]` | NDS5-04 | Create `parse_onet_technology()` parser in `onet.py`: handle the different column structure (T2 Type, T2 Example, Commodity Code, Commodity Title — no Scale ID, Data Value, N) | | |
| `[ ]` | NDS5-05 | Create `OnetTechnologyRow` dataclass with fields: occupation_code, t2_type, example_name, commodity_code, commodity_title, source_release_id, parser_version | | |
| `[ ]` | NDS5-06 | Add loader functions: `load_dim_technology()` and `load_bridge_occupation_technology()` | | |
| `[ ]` | NDS5-07 | Wire technology skills into `onet_refresh()` pipeline | | |
| `[ ]` | NDS5-08 | Add `/api/occupations/{soc_code}/technology` endpoint: return tools grouped by `t2_type` (Tools vs Technology) | | |
| `[ ]` | NDS5-09 | Add `loadTechnology()` function in `occupation.js`: render as grouped list (Tools heading + list, Technology heading + list) | | |
| `[ ]` | NDS5-10 | Add "Tools & Technology" section in `occupation.html` | | |
| `[ ]` | NDS5-11 | Add technology endpoint to `build_static.py` per-occupation JSON generation | | |
| `[ ]` | NDS5-12 | Add unit tests: parser handles Technology Skills column structure, loader deduplicates | | |
| `[ ]` | NDS5-13 | Add web tests: endpoint returns 200 with grouped data, profile page has technology section | | |
| `[ ]` | NDS5-14 | Run pipeline and verify technology data loads with real data | | |

---

## Phase NDS6: BLS CPI-U Inflation Adjustment (DS-06)

Add CPI data and real (inflation-adjusted) wage metrics.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS6-01 | Create migration SQL: `dim_price_index` table (price_index_key, series_id, series_name, base_period, seasonally_adjusted, source_release_id), sequence | | |
| `[ ]` | NDS6-02 | Create migration SQL: `fact_price_index_observation` table (observation_key, price_index_key, period_key FK, index_value, source_release_id, run_id), unique index on (price_index_key, period_key) | | |
| `[ ]` | NDS6-03 | Add manifest entry for `bls_cpi` in `source_manifest.yaml` pointing to `https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems` | | |
| `[ ]` | NDS6-04 | Create `src/jobclass/parse/cpi.py` with `parse_cpi()`: filter to series `CUSR0000SA0`, period `M13` (annual average), extract year + value. Handle whitespace-padded columns | | |
| `[ ]` | NDS6-05 | Create `CpiRow` dataclass with fields: series_id, year, period, value, source_release_id, parser_version | | |
| `[ ]` | NDS6-06 | Create staging table `stage__bls__cpi` and staging loader | | |
| `[ ]` | NDS6-07 | Create `src/jobclass/load/cpi.py` with `load_dim_price_index()` and `load_fact_price_index_observation()` | | |
| `[ ]` | NDS6-08 | Create `cpi_refresh()` pipeline function in `pipelines.py` and wire into `run_all.py` (runs after OEWS, before timeseries_refresh) | | |
| `[ ]` | NDS6-09 | Register `real_mean_annual_wage` and `real_median_annual_wage` in `dim_metric` with `derivation_type = 'derived'`, `units = 'dollars'`, `display_format = '$#,##0'` | | |
| `[ ]` | NDS6-10 | Add `compute_real_wages()` derivation step in `timeseries_refresh.py`: join nominal wage observations to CPI observations on period_key, apply deflation formula `nominal × (CPI_base / CPI_year)`, insert into `fact_derived_series` | | |
| `[ ]` | NDS6-11 | Choose and document the base year for deflation (e.g., 2023 = latest year with data). Store base year in a config constant | | |
| `[ ]` | NDS6-12 | Add "Real Mean Annual Wage" and "Real Median Annual Wage" options to metric dropdowns in Trend Explorer and Ranked Movers HTML templates | | |
| `[ ]` | NDS6-13 | Add per-metric trend files for real wages to `build_static.py` per-occupation generation | | |
| `[ ]` | NDS6-14 | Add unit tests: CPI parser extracts correct year + value from sample data, handles whitespace padding | | |
| `[ ]` | NDS6-15 | Add unit tests: deflation formula produces known values (e.g., $100,000 in 2021 → expected 2023 dollars) | | |
| `[ ]` | NDS6-16 | Add web tests: real wage metrics appear in trend API response, trend explorer page has real wage options | | |
| `[ ]` | NDS6-17 | Run pipeline and verify: CPI loads, real wages computed, trend explorer shows real wage series for a known occupation | | |

---

## Phase NDS7: SOC 2010↔2018 Crosswalk (DS-07)

Add the crosswalk and extend comparable history with pre-2018 OEWS vintages.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS7-01 | Create migration SQL: `bridge_soc_crosswalk` table (crosswalk_key, source_soc_code, source_soc_version, target_soc_code, target_soc_version, mapping_type, source_release_id), unique index on (source_soc_code, source_soc_version, target_soc_code, target_soc_version) | | |
| `[ ]` | NDS7-02 | Add manifest entry for `soc_crosswalk` in `source_manifest.yaml` pointing to `https://www.bls.gov/soc/2018/soc_2018_crosswalk.xlsx` | | |
| `[ ]` | NDS7-03 | Create `parse_soc_crosswalk()` in `soc.py`: read XLSX, extract 2010↔2018 code pairs, classify mapping type (1:1, split, merge, complex) by computing cardinality of each source and target code | | |
| `[ ]` | NDS7-04 | Create `CrosswalkRow` dataclass with fields: source_soc_code, source_soc_version, target_soc_code, target_soc_version, mapping_type, source_release_id, parser_version | | |
| `[ ]` | NDS7-05 | Create loader `load_bridge_soc_crosswalk()` in `src/jobclass/load/soc.py` with idempotent delete-before-insert | | |
| `[ ]` | NDS7-06 | Load SOC 2010 occupations into `dim_occupation` with `soc_version = '2010'`, `is_current = false`. Source: crosswalk file contains 2010 titles | | |
| `[ ]` | NDS7-07 | Add OEWS 2017 national + state manifest entries (first pre-2018 vintage to integrate) | | |
| `[ ]` | NDS7-08 | Verify OEWS 2017 parser handles column variations (check `_OEWS_COLUMN_ALIASES` in `oews.py`) | | |
| `[ ]` | NDS7-09 | Run OEWS 2017 extraction and verify staging tables contain rows tagged with 2017 source_release_id | | |
| `[ ]` | NDS7-10 | Modify `build_comparable_history()` in `timeseries_refresh.py`: for 1:1 crosswalk mappings, create comparable-history observations that remap SOC 2010 occupation_keys to SOC 2018 occupation_keys | | |
| `[ ]` | NDS7-11 | For split/merge mappings with employment_count: sum component values when building comparable-history rows. Tag with `mapping_type = 'aggregated'` | | |
| `[ ]` | NDS7-12 | For split/merge mappings with wage metrics: only include 1:1 mappings. Wage averages cannot be meaningfully combined without employment weights in the initial release | | |
| `[ ]` | NDS7-13 | Add OEWS 2012–2016 national + state manifest entries (10 additional entries) | | |
| `[ ]` | NDS7-14 | Run full pipeline with all OEWS vintages 2012–2023 and verify time-series extends back to 2012 for 1:1 mapped occupations | | |
| `[ ]` | NDS7-15 | Add unit tests: crosswalk parser classifies known mappings correctly (test 1:1, split, merge, complex examples) | | |
| `[ ]` | NDS7-16 | Add unit tests: comparable history builder remaps occupation keys through crosswalk | | |
| `[ ]` | NDS7-17 | Add warehouse tests: verify Trend Explorer shows 2012–2023 data for a 1:1 mapped occupation | | |
| `[ ]` | NDS7-18 | Add warehouse tests: verify split/merge occupations have employment comparable history but not wage comparable history | | |
| `[ ]` | NDS7-19 | Verify on live server: Trend Explorer for a known occupation (e.g., 15-1252 Software Developers) shows a longer time-series | | |

---

## Phase NDS8: Integration Testing & Deployment

Final verification across all new sources.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | NDS8-01 | Run `ruff check src/ tests/` and `ruff format --check src/ tests/` — all clean | | |
| `[ ]` | NDS8-02 | Run `pytest tests/unit/ tests/web/ -q` — all tests pass | | |
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

---

## Phase Summary

| Phase | Description | Task Count | Status |
|-------|-------------|------------|--------|
| NDS1 | Surface O\*NET Knowledge (DS-01) | 7 | Not Started |
| NDS2 | Surface O\*NET Abilities (DS-02) | 7 | Not Started |
| NDS3 | O\*NET Work Activities (DS-03) | 12 | Not Started |
| NDS4 | O\*NET Education & Training (DS-04) | 14 | Not Started |
| NDS5 | O\*NET Technology Skills (DS-05) | 14 | Not Started |
| NDS6 | BLS CPI-U Inflation Adjustment (DS-06) | 17 | Not Started |
| NDS7 | SOC 2010↔2018 Crosswalk (DS-07) | 19 | Not Started |
| NDS8 | Integration Testing & Deployment | 12 | Not Started |
| **Total** | | **102** | |

---

## Notes

- **NDS1 and NDS2 have zero dependencies** and require no new downloads. They should be implemented first as quick wins.
- **NDS3 through NDS5 are independent** of each other. They all require O\*NET downloads but use separate files. They can be developed in parallel.
- **NDS6 (CPI) is independent** of all O\*NET work. It can start at any time.
- **NDS7 (Crosswalk) is the most complex phase** and has the highest risk. The crosswalk mapping classification and comparable-history extension involve non-trivial logic. Start after NDS1/NDS2 are validated.
- **NDS8 depends on all prior phases** completing. This is the final integration gate.
- **Incremental deployment is encouraged.** Each phase can be committed, pushed, and deployed independently. The static site should be rebuilt after each phase that adds new API endpoints.
- **OEWS vintage expansion (NDS7)** adds 12 new manifest entries (6 years × 2 files). This significantly increases pipeline run time. Consider adding a `--vintage` CLI flag to run specific vintages rather than all.
- **O\*NET version updates** (e.g., 29.1 → 30.0) may change file URLs. The manifest entries should use the version number in comments so they can be updated when a new O\*NET release drops.
