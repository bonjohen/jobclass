# Inflation Adjustment with CPI

## The Lesson

Comparing nominal wages across years is misleading because the dollar's purchasing power changes over time. Converting to constant dollars using CPI-U deflation separates genuine labor market shifts from background price-level changes and is essential for any multi-vintage wage trend analysis.

## Context

A labor market data warehouse held three vintages of OEWS wage data (2021, 2022, 2023). The Trend Explorer page showed wage trends over time, but without inflation adjustment, every occupation appeared to have rising wages simply because the dollar was worth less each year. Comparing $50,000 in 2021 to $52,000 in 2023 looks like a 4% raise, but if inflation was 10% over that period, the worker's purchasing power actually fell. The pipeline needed to produce inflation-adjusted "real" wages alongside the nominal values.

## What Happened

1. **CPI-U data was ingested.** The Bureau of Labor Statistics publishes the Consumer Price Index for All Urban Consumers (CPI-U), which measures average price changes over time. The pipeline ingested CPI-U annual averages to serve as the deflation reference.

2. **A base year was selected.** The project uses `CPI_BASE_YEAR = 2023` — the latest complete year with published CPI-U data. All real wage values are denominated in "2023 dollars," making them directly comparable to the most recent nominal wages in current BLS publications.

3. **The deflation formula was implemented as a single SQL INSERT...SELECT.** The `compute_real_wages` function joins wage observations with their corresponding CPI values through the time dimension:

   ```
   real_wage = nominal_wage x (CPI_base_year / CPI_observation_year)

   Example:
     Nominal wage 2021:     $50,000
     CPI-U 2021:            270.970
     CPI-U 2023 (base):     304.702
     Real wage (2023$):     $50,000 x (304.702 / 270.970) = $56,226
   ```

   ```sql
   INSERT INTO fact_derived_series (...)
   SELECT
       real_metric_key,
       nominal_metric_key,
       obs.occupation_key, obs.geography_key,
       obs.period_key, obs.comparability_mode,
       ROUND(obs.observed_value * (base_cpi / fpi.index_value), 0),
       'cpi_deflation', run_id
   FROM fact_time_series_observation obs
   JOIN dim_time_period tp ON obs.period_key = tp.period_key
   JOIN fact_price_index_observation fpi
       ON fpi.period_key = obs.period_key
   WHERE obs.observed_value IS NOT NULL
     AND fpi.index_value > 0
   ```

   The `WHERE` clause guards against division by zero and NULL propagation. Results are rounded to whole dollars since sub-dollar precision in annual wages is spurious.

4. **Two derived wage metrics were produced.** Each is paired with its nominal counterpart and stored in `fact_derived_series` with `derivation_method = 'cpi_deflation'`:

   | Metric | Base Metric | Formula |
   |---|---|---|
   | real_mean_annual_wage | mean_annual_wage | nominal x (CPI_2023 / CPI_year) |
   | real_median_annual_wage | median_annual_wage | nominal x (CPI_2023 / CPI_year) |

   They are never mixed with base observations in `fact_time_series_observation` — the separation ensures downstream queries always know whether they are working with nominal or real values based on which table they read from.

## Key Insights

- **Changing the base year shifts all values proportionally but does not change relative ordering or growth rates.** A $56,226 real wage in 2023 dollars becomes roughly $52,000 in 2021 dollars — same purchasing power, different unit.
- **The formula scales older wages up, not recent wages down.** Since prices were lower in earlier years, the CPI ratio for past years is greater than 1.0. The base year ratio is exactly 1.0, so base-year nominal and real wages are identical.
- **Derived series are fully regenerated, not migrated.** Because `fact_derived_series` is rebuilt on each time-series refresh, updating the base year requires only changing the constant and re-running — no migration needed.
- **Nominal and real wages belong in separate tables.** Storing them together would require every downstream query to check a flag. Separate tables make the distinction structural rather than conditional.

## Related Lessons

- [Time-Series Normalization](06-time-series-normalization.md)
- [Derived Metrics from Base Observations](18-derived-metrics.md)
- [Multi-Vintage Query Pitfalls](12-multi-vintage-queries.md)
