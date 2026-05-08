# Derived Metrics from Base Observations

## The Lesson

Base observations are source truth; derived values are computed artifacts. Mixing them in the same table creates ambiguity about whether a number is a measurement or a calculation. Separating them into distinct tables — with explicit derivation methods and base-metric linkage — makes the distinction structural rather than conditional and enables safe idempotent recomputation.

## Context

A labor market data warehouse stored multi-vintage OEWS observations (employment counts, mean wages, median wages) in `fact_time_series_observation`. The Trend Explorer and Ranked Movers pages needed year-over-year changes, rolling averages, real wages, state-vs-national gaps, and rank deltas — all computed from the base observations. These derived values needed a home that would not contaminate source truth and would support independent recomputation of each metric.

## What Happened

1. **A separate `fact_derived_series` table was created.** Each derived row carries a `derivation_method` label (e.g., `'yoy_absolute_change'`, `'cpi_deflation'`) and a `base_metric_key` pointing back to the source observation metric. Downstream queries always know what kind of value they are working with based on which table they read from.

2. **Year-over-year change was implemented as a self-join through the time dimension.** The core pattern connects each observation to its prior-year counterpart:

   ```sql
   INSERT INTO fact_derived_series (...)
   SELECT
       derived_key, base_key,
       curr.occupation_key, curr.geography_key,
       curr.period_key, curr.comparability_mode,
       curr.observed_value - prev.observed_value,
       'yoy_absolute_change', run_id
   FROM fact_time_series_observation curr
   JOIN dim_time_period tp_curr ON curr.period_key = tp_curr.period_key
   JOIN dim_time_period tp_prev ON tp_prev.year = tp_curr.year - 1
   JOIN fact_time_series_observation prev
     ON prev.metric_key = curr.metric_key
     AND prev.occupation_key = curr.occupation_key
     AND prev.geography_key = curr.geography_key
     AND prev.period_key = tp_prev.period_key
   WHERE curr.observed_value IS NOT NULL
     AND prev.observed_value IS NOT NULL
   ```

   The join on `metric_key`, `occupation_key`, `geography_key`, and `period_key` ensures each comparison is exact. If either year is missing or NULL, no derived value is produced — the pipeline never imputes.

3. **Rolling averages were built with a triple-join extension.** A 3-year rolling average connects three consecutive years. The triple-join naturally handles the "3 consecutive years required" constraint — if any year is missing, the JOIN produces no rows:

   ```sql
   JOIN dim_time_period tp_1 ON tp_1.year = tp_curr.year - 1
   JOIN dim_time_period tp_2 ON tp_2.year = tp_curr.year - 2
   ...
   ROUND((p2.observed_value + p1.observed_value + curr.observed_value) / 3.0, 2)
   ```

4. **Idempotent delete-before-insert was adopted for all derived metrics.** Every compute function deletes all existing rows for its metric key, then inserts freshly computed values:

   ```python
   derived_key = get_metric_key(conn, "yoy_absolute_change")
   conn.execute("DELETE FROM fact_derived_series WHERE metric_key = ?", [derived_key])
   conn.execute("INSERT INTO fact_derived_series (...) SELECT ...")
   ```

   The delete is scoped to a single `metric_key`, so recomputing YoY change does not touch rolling averages or real wages.

5. **Seven derived metrics were registered.** Each has a specific derivation method and minimum data requirement:

   | Metric | Units | Method | Min Data Required |
   |---|---|---|---|
   | yoy_absolute_change | varies | Self-join on year-1 | 2 consecutive years |
   | yoy_percent_change | percent | (curr - prev) / prev x 100 | 2 consecutive years |
   | rolling_avg_3yr | varies | Average of 3 consecutive years | 3 consecutive years |
   | state_vs_national_gap | varies | state_value - national_value | State + national data |
   | rank_delta | rank_change | rank(year-1) - rank(year) | 2 consecutive years |
   | real_mean_annual_wage | dollars | CPI deflation | CPI data for year |
   | real_median_annual_wage | dollars | CPI deflation | CPI data for year |

## Key Insights

- **Delete-before-insert is safe for derived metrics because every value is fully reproducible.** Unlike base data (which could be lost), derived data can always be recomputed from base observations. This makes the pipeline idempotent: running it twice produces the same result.
- **Inner join semantics provide free gap detection.** Requiring N consecutive values by adding N-1 self-joins through the time dimension means the database engine handles the absence check automatically. No explicit gap detection code is needed.
- **Each derived metric is an independent computation.** Scoping the delete to a single `metric_key` means any metric can be recomputed in isolation without affecting others in the table.
- **The `base_metric_key` linkage enables traceability.** Every derived row points back to the source observation metric it was computed from, making it possible to trace exactly how any value was produced.

## Related Lessons

- [Inflation Adjustment with CPI](15-inflation-adjustment.md)
- [Time-Series Normalization](06-time-series-normalization.md)
- [Idempotent Pipelines](07-idempotent-pipelines.md)
