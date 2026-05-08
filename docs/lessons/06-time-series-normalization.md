# Time-Series Normalization

## The Lesson

Fact tables store snapshots — single measurements at single points in time. Time-series analysis requires a separate normalization step that aligns snapshots across periods into a conformed schema with explicit metric definitions, and a further separation between base observations and derived series to prevent circular computation.

## Context

The JobClass warehouse stores employment and wage data from three OEWS vintages (2021, 2022, 2023) in `fact_occupation_employment_wages`. Each row records what one OEWS release said about one occupation in one geography. To answer trend questions ("how has employment changed?"), these individual snapshots needed to be restructured into time-aligned series with a formal metric catalog, plus derived computations like year-over-year change and rolling averages.

## What Happened

1. **A time-series schema was designed alongside the fact table.** Four new structures were introduced: `dim_time_period` (year, period type), `dim_metric` (metric name, display name, unit), `fact_time_series_observation` (base measurements aligned by period and metric), and `fact_derived_series` (computed values stored separately from source data).
2. **Base observations were extracted from the fact table.** The normalization query pivots `fact_occupation_employment_wages` rows into `(occupation_key, geography_key, period_key, metric_key, value)` tuples — one row per metric per period, rather than one wide row with multiple measurement columns.
3. **Two analysis modes were implemented.** "As Published" preserves every observation exactly as it appeared in its source release, regardless of taxonomy changes. "Comparable History" restricts observations to vintages sharing the same SOC taxonomy version (currently SOC 2018 for all three loaded vintages). Both modes are always computed; the UI lets users choose.
4. **Derived metrics were computed from base observations only.** Five derived metrics were defined:

   | Metric | Formula | Minimum Data Required |
   |--------|---------|----------------------|
   | Year-over-year absolute change | `value(year) - value(year-1)` | 2 consecutive years |
   | Year-over-year percent change | `(value(year) - value(year-1)) / value(year-1) x 100` | 2 consecutive years |
   | 3-year rolling average | `avg(value) over 3-year window` | 3 consecutive years |
   | State vs. national gap | `state_value - national_value` | State + national data |
   | Rank delta | `rank(year-1) - rank(year)` | 2 consecutive years |

5. **Derived values were stored in a separate fact table.** `fact_derived_series` is structurally identical to `fact_time_series_observation` but explicitly marked as computed. This prevents derived values from being fed back into derivation logic (no circular computation) and makes it clear in queries which values are source measurements and which are calculated.

## Key Insights

- **Snapshots and series are different data products.** A fact table row saying "employment was 200,480 in 2023" is a snapshot. A time series saying "employment grew from 195,000 to 200,480 over three years" requires aligning multiple snapshots and computing deltas. These are separate analytical concerns and deserve separate storage.
- **Derived values must never mix with source observations.** Storing year-over-year change in the same table as base employment counts creates a risk of computing "change of change" or averaging derived values with raw values. A separate `fact_derived_series` table eliminates this category of error by construction.
- **Both "as published" and "comparable" views should always be available.** Forcing users into one mode bakes a comparability opinion into the data layer. Computing both and letting the UI toggle between them preserves analytical flexibility and makes the comparability assumption explicit rather than hidden.
- **Derived metrics need minimum-data guards.** Year-over-year change requires two consecutive years; rolling averages require three. Computing these metrics when insufficient data exists produces misleading partial results. The pipeline checks data availability before computing each derived metric.

## Related Lessons

- [The Multi-Vintage Challenge](04-multi-vintage-challenge.md) — the dimension deduplication that makes cross-vintage alignment possible
- [Derived Metrics](18-derived-metrics.md) — deeper treatment of derived metric computation and edge cases
- [Inflation Adjustment](15-inflation-adjustment.md) — CPI-based real wage computation as another derived series
- [Multi-Vintage Queries](12-multi-vintage-queries.md) — query patterns for the normalized time-series schema
