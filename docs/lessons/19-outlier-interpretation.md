# Ranked Movers and Outlier Interpretation

## The Lesson

Percentage changes on small bases are statistically volatile and can dominate ranked lists even when the absolute economic impact is trivial. Any ranked-change display must show both percentage and absolute values so users can distinguish genuine labor market shifts from small-sample noise.

## Context

A labor market data warehouse computed year-over-year percent changes for every occupation across employment counts, mean wages, and median wages. The Ranked Movers page surfaced the top gainers (highest YoY percent change) and top losers (most negative) for a user-selected metric and year. The page was a discovery tool — users exploring wage trends would see a completely different set of occupations than those exploring employment shifts. But the initial implementation surfaced misleading results because it ranked solely by percentage.

## What Happened

1. **A dual-direction sort query was built.** Gainers and losers come from the same query with only the `ORDER BY` direction changed. The key join is through `base_metric_key`, which connects each YoY percent change back to the specific base metric the user selected:

   ```sql
   movers_sql = """
       SELECT o.soc_code, o.occupation_title,
              d.derived_value AS pct_change,
              abs.derived_value AS abs_change
       FROM fact_derived_series d
       JOIN dim_metric m ON d.metric_key = m.metric_key
       JOIN dim_metric bm ON d.base_metric_key = bm.metric_key
       JOIN dim_occupation o ON d.occupation_key = o.occupation_key
       ...
       WHERE m.metric_name = 'yoy_percent_change'
         AND bm.metric_name = ?
         AND tp.year = ?
       ORDER BY d.derived_value {direction}
       LIMIT ?
   """
   gainers = execute(movers_sql.format(direction="DESC"), params)
   losers  = execute(movers_sql.format(direction="ASC"), params)
   ```

   The `dim_metric` table is joined twice: once for the derived metric itself (`m`) and once for the base metric it was derived from (`bm`).

2. **Small-denominator volatility was identified as a systemic problem.** An occupation with 100 workers gaining 50 shows +50% YoY change, outranking an occupation with 100,000 workers gaining 5,000 (+5%). The percentage is mathematically correct in both cases, but the economic significance is vastly different:

   ```
   Dancers:                3,850 -> 8,930   (+131.9%)  # Volatile small base
   Software Developers:  1,795,300 -> 1,847,800  (+2.9%)   # Stable large base
   ```

3. **Absolute change was added alongside percentage.** The API returns both `pct_change` and `abs_change` so the UI shows both side by side. A +131.9% change in 5,080 jobs is less economically significant than a +2.9% change in 52,500 jobs.

4. **Suppressed data effects were documented.** When BLS suppresses a value in year N but not year N+1, the YoY calculation is NULL (the pipeline never imputes). But when suppression is lifted, the "first visible" year may show extreme apparent changes because it is being compared to a period with very different conditions. A +200% wage increase for Broadcast Announcers reflects small-sample volatility in a niche occupation, not a genuine doubling of the profession's pay.

5. **Year and metric filters were added with static site support.** The API returns `available_years` and defaults to the latest year. The static site pre-generates separate JSON files for each combination:

   ```
   movers.json                           # default (employment_count, latest year)
   movers_mean_annual_wage.json          # mean wage, latest year
   movers-2022.json                      # employment count, 2022
   movers-2022_median_annual_wage.json   # median wage, 2022
   ```

   The naming convention encodes both the year and the metric in the filename, allowing the JavaScript shim to translate query parameters into file paths.

## Key Insights

- **Always show absolute changes alongside percentages.** Without absolute context, users cannot tell whether a +200% change represents a $241,150 jump or a $150 fluctuation. The percentage alone is uninterpretable for decision-making.
- **Small-denominator volatility is structural, not a bug.** Niche occupations with few practitioners will always dominate percentage-based rankings. Showing both values lets users judge significance for themselves rather than hiding the noise.
- **Suppression boundaries create artificial outliers.** When a value crosses the suppression threshold between years, the first visible year may appear as an extreme mover. This is an artifact of the disclosure rules, not a labor market signal.
- **Different base metrics produce completely different rankings.** Employment volatility and wage volatility have different profiles. The double-join through `dim_metric` (once for the derived metric, once for the base) is what enables per-metric ranking from a single query structure.

## Related Lessons

- [Derived Metrics from Base Observations](18-derived-metrics.md)
- [Multi-Vintage Query Pitfalls](12-multi-vintage-queries.md)
- [Data Quality Traps in Government Sources](05-data-quality-traps.md)
