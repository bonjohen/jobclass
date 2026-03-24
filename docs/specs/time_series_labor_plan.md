# Phased Release Plan — Time-Series Labor Intelligence

This document tracks the work required to extend the JobClass warehouse from point-in-time occupation reporting into a time-series labor intelligence system, following the requirements in `time_series_labor_design.md`.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase TS1: Conformed Metric Catalog and Time-Period Dimension

Build the foundational reference tables that all downstream time-series work depends on.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS1-01 | Design and create `dim_metric` table: metric_key, metric_name, units, display_format, comparability_constraint, derivation_type, description | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-02 | Design and create `dim_time_period` table: period_key, period_type (annual/quarterly), year, quarter, period_start_date, period_end_date | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-03 | Populate `dim_metric` with Release 1 base metrics: employment_count, mean_annual_wage, median_annual_wage | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-04 | Populate `dim_metric` with projection-related base metrics: projected_employment, employment_change, employment_change_pct | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-05 | Populate `dim_time_period` with annual periods covering existing warehouse data range (all source release years present in facts) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-06 | Add migration step to `migrate` CLI command for TS1 tables | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-07 | Test: `dim_metric` has expected rows for all Release 1 metrics | 2026-03-23 | 2026-03-23 |
| `[X]` | TS1-08 | Test: `dim_time_period` covers all years present in existing fact tables | 2026-03-23 | 2026-03-23 |

---

## Phase TS2: Base Time-Series Observation Fact

Normalize existing warehouse facts into a single time-indexed observation table at the grain of metric + occupation + geography + period + source release + comparability mode.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS2-01 | Design and create `fact_time_series_observation` table: observation_key, metric_key, occupation_key, geography_key, period_key, source_release_id, comparability_mode, observed_value, suppression_flag, run_id | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-02 | Build normalizer for OEWS employment_count: extract from `fact_occupation_employment_wages` into observation rows | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-03 | Build normalizer for OEWS mean_annual_wage: extract from `fact_occupation_employment_wages` into observation rows | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-04 | Build normalizer for OEWS median_annual_wage: extract from `fact_occupation_employment_wages` into observation rows | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-05 | Build normalizer for projection measures: extract from `fact_occupation_projections` into observation rows | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-06 | Tag all normalized rows with `comparability_mode = 'as_published'` for initial load | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-07 | Ensure idempotent loading: re-running normalization for the same source release must not create duplicates | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-08 | Add migration step for `fact_time_series_observation` | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-09 | Test: observation row count matches expected extractions from source facts (cross-check totals) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-10 | Test: grain uniqueness — no duplicate (metric, occupation, geography, period, source_release, comparability_mode) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-11 | Test: all observation metric_keys exist in `dim_metric` | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-12 | Test: all observation period_keys exist in `dim_time_period` | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-13 | Test: all observation occupation_keys exist in `dim_occupation` | 2026-03-23 | 2026-03-23 |
| `[X]` | TS2-14 | Test: all observation geography_keys exist in `dim_geography` | 2026-03-23 | 2026-03-23 |

---

## Phase TS3: Multi-Vintage Data Extraction

Extend the pipeline to download and process multiple historical OEWS releases so the time-series has more than a single year.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS3-01 | Add multi-vintage OEWS URLs to `source_manifest.yaml` (at least 3 years: e.g. 2021, 2022, 2023) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-02 | Update extraction pipeline to iterate over multiple source releases per dataset | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-03 | Ensure parsers handle minor column variations across OEWS vintages | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-04 | Run `run-all` for multi-vintage OEWS and verify staging tables contain rows from all vintages | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-05 | Verify `fact_occupation_employment_wages` contains rows tagged to each source_release_id | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-06 | Re-run TS2 normalizers — verify `fact_time_series_observation` contains multi-year observations | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-07 | Test: observation table has >= 3 distinct period_keys for employment_count at national level | 2026-03-23 | 2026-03-23 |
| `[X]` | TS3-08 | Test: a known occupation (e.g. 15-1251) has observations for all extracted vintages | 2026-03-23 | 2026-03-23 |

---

## Phase TS4: Comparable History Series

Build comparable-history products that account for SOC taxonomy changes across vintage years.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS4-01 | Design comparable-history logic: define rules for when two vintages share the same SOC version and can be directly compared | 2026-03-23 | 2026-03-23 |
| `[X]` | TS4-02 | Add `comparability_mode = 'comparable'` observation rows for vintages sharing the same SOC version | 2026-03-23 | 2026-03-23 |
| `[X]` | TS4-03 | Add metadata to `dim_metric` indicating which metrics support comparable-history mode | 2026-03-23 | 2026-03-23 |
| `[X]` | TS4-04 | Add validation: comparable-mode observations must not be built from vintages spanning a SOC version break | 2026-03-23 | 2026-03-23 |
| `[X]` | TS4-05 | Test: comparable-mode observation count <= as-published observation count (subset relationship) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS4-06 | Test: no comparable-mode observation exists for a metric flagged as non-comparable | 2026-03-23 | 2026-03-23 |

---

## Phase TS5: Derived Metric Library

Compute trend metrics from base observations and store them in a separate derived-series fact.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS5-01 | Design and create `fact_derived_series` table: derived_key, metric_key, base_metric_key, occupation_key, geography_key, period_key, comparability_mode, derived_value, derivation_method, run_id | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-02 | Register derived metrics in `dim_metric`: yoy_absolute_change, yoy_percent_change, rolling_avg_3yr, state_vs_national_gap, rank_delta | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-03 | Implement year-over-year absolute change computation | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-04 | Implement year-over-year percent change computation | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-05 | Implement 3-year rolling average computation | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-06 | Implement state-versus-national gap computation (state value minus national value for same metric, occupation, period) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-07 | Implement rank change over time: rank occupations by metric within geography per period, compute rank delta | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-08 | Implement projection gap: difference between most recent observed value and projected value | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-09 | Add `requires_comparable_input` flag to each derived metric definition; enforce during computation | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-10 | Ensure idempotent derived-series loading | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-11 | Add migration step for `fact_derived_series` | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-12 | Test: derived row count is plausible relative to observation count | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-13 | Test: yoy_percent_change for a known occupation matches hand-calculated value | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-14 | Test: state_vs_national_gap values sum correctly (spot check) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-15 | Test: rolling_avg_3yr is null when fewer than 3 years of data exist | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-16 | Test: no derived row references a base metric that does not exist in observations | 2026-03-23 | 2026-03-23 |
| `[X]` | TS5-17 | Test: derived metrics flagged `requires_comparable_input` have no rows built from as-published-only series | 2026-03-23 | 2026-03-23 |

---

## Phase TS6: Time-Series Pipeline Orchestration

Wire the new time-series stages into the existing pipeline framework.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS6-01 | Create `src/jobclass/orchestrate/timeseries_refresh.py` with `timeseries_refresh(conn)` entry point | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-02 | Orchestrate: populate `dim_metric` -> populate `dim_time_period` -> normalize observations -> build comparable history -> compute derived series | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-03 | Integrate `timeseries_refresh` into `run_all_pipelines()` — runs after `warehouse_publish()` | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-04 | Add `timeseries-refresh` CLI subcommand for standalone execution | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-05 | Add progress logging: step name, row counts, and elapsed time for each stage | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-06 | Handle partial failure: if derived computation fails, base observations remain intact | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-07 | Test: `run-all` completes with timeseries stages included | 2026-03-23 | 2026-03-23 |
| `[X]` | TS6-08 | Test: `timeseries-refresh` is idempotent — running twice produces same row counts | 2026-03-23 | 2026-03-23 |

---

## Phase TS7: Time-Series Validation

Add validation rules specific to time-series data quality.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS7-01 | Validate series continuity: flag occupations with gaps in expected annual periods | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-02 | Validate period ordering: no observation has period_start_date after period_end_date | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-03 | Validate no duplicate periods within a series (metric + occupation + geography + comparability_mode) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-04 | Validate missing expected periods: for national-level base metrics, every extracted vintage should be represented | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-05 | Validate derived-series correctness: recompute a sample of derived values and compare | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-06 | Validate comparable-only constraint: no derived metric flagged `requires_comparable_input` was built from non-comparable observations | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-07 | Validate clear separation: no observation row has a derived metric_key; no derived row has a base metric_key | 2026-03-23 | 2026-03-23 |
| `[X]` | TS7-08 | Validate real data coverage: at least one occupation has a complete multi-year trend for each base metric at national level | 2026-03-23 | 2026-03-23 |

---

## Phase TS8: Reporting Marts

Build denormalized marts for analyst and website consumption.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS8-01 | Design and create `mart_occupation_trend_series` view: occupation, metric, geography, period, observed_value, yoy_change, yoy_pct_change, rolling_avg, comparability_mode, lineage | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-02 | Design and create `mart_occupation_geography_gap_series` view: occupation, metric, state, period, state_value, national_value, gap, comparability_mode | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-03 | Design and create `mart_occupation_rank_change` view: occupation, metric, geography, period, rank, prior_rank, rank_delta | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-04 | Design and create `mart_occupation_projection_context` view: occupation, metric, last_observed_value, last_observed_period, projected_value, projection_year, projection_gap | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-05 | Design and create `mart_occupation_similarity_trend_overlay` view: seed occupation, similar occupation, metric, period, seed_value, similar_value | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-06 | Register all new marts in `MART_VIEWS` list for warehouse_publish | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-07 | Test: `mart_occupation_trend_series` returns rows for a known occupation | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-08 | Test: `mart_occupation_geography_gap_series` returns state-level rows | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-09 | Test: `mart_occupation_rank_change` returns rows with non-null rank_delta | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-10 | Test: `mart_occupation_projection_context` returns rows with projection_gap values | 2026-03-23 | 2026-03-23 |
| `[X]` | TS8-11 | Test: all mart views preserve lineage, comparability_mode, and metric identity columns | 2026-03-23 | 2026-03-23 |

---

## Phase TS9: Website — Trend Explorer and Comparison Pages

Build the user-facing website pages for time-series analysis.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | TS9-01 | Add top-level "Trends" or "Analysis" navigation area to the site layout | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-02 | Build trend explorer page: select one occupation, display metric time-series chart with observed vs. projected distinction | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-03 | Trend explorer: show metric name, units, time grain, comparability mode, and lineage context on the page | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-04 | Trend explorer: visually distinguish projected values from observed values (dashed line, color, label) | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-05 | Trend explorer: label derived values as derived | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-06 | Build occupation comparison page: select multiple occupations, compare same metric over same period range | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-07 | Build geography comparison page: select one occupation, compare metric across states for a given period | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-08 | Build ranked movers page: show top gainers and losers by selected metric over a user-selected period range | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-09 | Extend methodology page: explain comparability mode, derived metrics, revision handling, and discontinuities | 2026-03-23 | 2026-03-23 |
| `[X]` | TS9-10 | Add data queries backing each page: wire pages to the TS8 mart views | 2026-03-23 | 2026-03-23 |

---

## Phase TS10: Real Data End-to-End Verification

Run the full pipeline and website against real data and verify key user flows.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | TS10-01 | Run `jobclass-pipeline run-all` with timeseries stages — all stages succeed | | |
| `[ ]` | TS10-02 | Verify `jobclass-pipeline status` shows non-zero row counts for all time-series tables | | |
| `[ ]` | TS10-03 | Start `jobclass-web` and verify trend explorer loads with real multi-year data for a known occupation | | |
| `[ ]` | TS10-04 | Verify occupation comparison page renders with real data for at least 3 occupations | | |
| `[ ]` | TS10-05 | Verify geography comparison page renders with real state-level data | | |
| `[ ]` | TS10-06 | Verify ranked movers page shows real gainers/losers with plausible values | | |
| `[ ]` | TS10-07 | Verify methodology page accurately describes time-series data products | | |
| `[ ]` | TS10-08 | Trace one end-to-end example from raw extraction through visible website output (document the occupation, metric, and values) | | |
| `[ ]` | TS10-09 | Verify projected values are visually distinct from observed values on trend explorer | | |
| `[ ]` | TS10-10 | Verify derived values are labeled as derived on all pages where they appear | | |
| `[ ]` | TS10-11 | Fix any data issues, column mismatches, or rendering bugs discovered during verification | | |

---

## Phase Summary

| Phase | Description | Task Count | Completed |
|-------|-------------|------------|-----------|
| TS1 | Conformed Metric Catalog and Time-Period Dimension | 8 | 8 |
| TS2 | Base Time-Series Observation Fact | 14 | 14 |
| TS3 | Multi-Vintage Data Extraction | 8 | 8 |
| TS4 | Comparable History Series | 6 | 6 |
| TS5 | Derived Metric Library | 17 | 17 |
| TS6 | Time-Series Pipeline Orchestration | 8 | 8 |
| TS7 | Time-Series Validation | 8 | 8 |
| TS8 | Reporting Marts | 11 | 11 |
| TS9 | Website — Trend Explorer and Comparison Pages | 10 | 10 |
| TS10 | Real Data End-to-End Verification | 11 | 0 |
| **Total** | | **101** | **90** |

---

## Notes

- **TS1 must complete before TS2** — observations reference both `dim_metric` and `dim_time_period`.
- **TS2 must complete before TS5** — derived metrics are computed from base observations.
- **TS3 can start in parallel with TS1/TS2** — multi-vintage extraction is independent of the time-series schema, but TS2 normalization depends on TS3 data being available.
- **TS4 depends on TS2 and TS3** — comparable history requires multi-vintage observations to exist.
- **TS5 depends on TS2 and TS4** — some derived metrics require comparable-history inputs.
- **TS6 depends on TS1–TS5** — orchestration wires together all prior stages.
- **TS7 can begin once TS2 is loaded** — validation rules apply progressively as more data arrives.
- **TS8 depends on TS5 and TS6** — marts query both base and derived facts.
- **TS9 depends on TS8** — website pages are backed by mart views.
- **TS10 depends on all prior phases** — this is the final end-to-end verification.
- **Multi-vintage OEWS**: BLS publishes annual OEWS files going back several years. Not all vintages may have identical column layouts; parser flexibility (TS3-03) is required.
- **SOC version breaks**: The SOC taxonomy was revised in 2018. Vintages before and after a revision cannot be directly compared without crosswalk logic. TS4 initially handles the simpler case of vintages within the same SOC version.
- **Projection measures** are inherently non-comparable across vintages (different base years and projection horizons). The comparable-history constraint in TS4 should exclude projection metrics.
- **Real data acceptance** (TS10) is a hard requirement per the design document — "working" means visible on the website with real data, not just passing tests.
- The existing fixture-based test suite remains in place for regression. Time-series tests (TS2, TS5, TS7) should run against a populated warehouse using a separate pytest marker or conftest, consistent with the RD5 approach.
