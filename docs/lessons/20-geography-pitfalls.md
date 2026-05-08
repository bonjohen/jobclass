# Geography Comparison Pitfalls

## The Lesson

Geographic wage comparisons are inherently incomplete: nominal gaps do not account for cost-of-living differences, suppressed cells create invisible holes in small-occupation maps, and the same query pattern must work across national, state, and metro levels without separate code paths. A dimension-driven geography model handles the structural challenge, but the interpretive caveats must be surfaced to users explicitly.

## Context

A labor market data warehouse stored OEWS wage observations at national and state levels, linked through `dim_geography` with a `geo_type` classifier. The web application offered a geography comparison view that showed how each state's wage for a given occupation differed from the national average. Three pitfalls emerged: cost-of-living confounders that made nominal gaps misleading, suppressed cells that made small-occupation comparisons incomplete, and the need for a geography model flexible enough to add new levels without schema changes.

## What Happened

1. **A state-vs-national gap metric was computed.** A single INSERT...SELECT pairs each state observation with the corresponding national observation for the same occupation, metric, and period:

   ```sql
   INSERT INTO fact_derived_series (...)
   SELECT
       derived_key, base_key,
       state_obs.occupation_key, state_obs.geography_key,
       state_obs.period_key, state_obs.comparability_mode,
       state_obs.observed_value - nat_obs.observed_value,
       'state_vs_national_gap', run_id
   FROM fact_time_series_observation state_obs
   JOIN dim_geography g ON state_obs.geography_key = g.geography_key
   JOIN dim_geography g_nat ON g_nat.geo_type = 'national'
   JOIN fact_time_series_observation nat_obs
     ON nat_obs.occupation_key = state_obs.occupation_key
     AND nat_obs.geography_key = g_nat.geography_key
     AND nat_obs.period_key = state_obs.period_key
   WHERE g.geo_type = 'state'
     AND state_obs.observed_value IS NOT NULL
     AND nat_obs.observed_value IS NOT NULL
   ```

   A positive gap means the state pays more than the national average; negative means less. The `IS NOT NULL` filters exclude suppressed values so the derived series only contains gaps where both sides have real data.

2. **A year-resolution pattern was implemented in the API.** If the caller does not specify a year, the endpoint automatically finds the latest available year. This ensures users always see data even when different vintages have different latest years.

3. **Cost-of-living confounders were identified as unsolvable within the data.** California's software developers earn roughly $20K above the national average, but San Francisco housing costs $30K more per year. A positive gap in nominal wages can mask a negative gap in purchasing power. The Bureau of Economic Analysis publishes Regional Price Parities (RPPs) that could adjust for geographic cost differences, but the warehouse does not ingest RPP data. An explicit caveat was added: all geographic wage comparisons are nominal.

4. **Suppressed cells were documented for small-occupation comparisons.** States with few workers in a given occupation have suppressed OEWS data:

   | Occupation | States with data | States suppressed |
   |---|---|---|
   | Registered Nurses (29-1141) | 51 | 0 |
   | Software Developers (15-1252) | 51 | 0 |
   | Dancers (27-2031) | 12 | 39 |
   | Astronomers (19-2011) | 7 | 44 |

   The API returns only non-NULL values — suppressed states simply do not appear. A map for "Dancers" would have 39 blank states, which could be mistaken for zero employment rather than suppressed data. The distinction matters: suppressed means "data exists but cannot be disclosed," not "no workers in this state."

5. **A dimension-driven geography model was adopted.** A single `dim_geography` table with a `geo_type` classifier enables level-based filtering without separate tables:

   ```
   dim_geography:
     geo_key | geo_type  | geo_code | geo_name
     1       | national  | US       | National
     2       | state     | CA       | California
     3       | state     | NY       | New York
     4       | metro     | 31080    | Los Angeles-Long Beach-Anaheim
   ```

   Adding a new geography level (e.g., county) requires no schema changes — just new rows in `dim_geography`. The fact tables do not know or care what kind of geography they point to; the dimension carries that context.

## Key Insights

- **A positive wage gap signals higher pay, not higher purchasing power.** Without cost-of-living adjustment, geographic wage comparisons are nominal only. Users must bring their own context to interpret these numbers.
- **Suppressed is not zero.** BLS suppresses cells to protect confidentiality when respondent counts are too small. Map visualizations must distinguish between "no data disclosed" and "no workers exist" — they are different facts with different implications.
- **Explicit type columns beat separate tables.** A `dim_state` and a `dim_metro` table would force every query to know which table to join. A single `dim_geography` with a `geo_type` filter lets the same SQL work for any geography level, and adding new levels requires no schema changes.
- **Default to the latest available year.** Different data vintages may have different latest years. Resolving the year within the context of the specific query ensures users always see data without needing to know which vintages are loaded.

## Related Lessons

- [Dimensional Modeling for Labor Data](03-dimensional-modeling.md)
- [Inflation Adjustment with CPI](15-inflation-adjustment.md)
- [Data Quality Traps in Government Sources](05-data-quality-traps.md)
