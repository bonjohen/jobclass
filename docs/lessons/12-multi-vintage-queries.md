# Multi-Vintage Query Pitfalls

## The Lesson

Once a warehouse holds multiple vintages of the same dataset, every query must explicitly decide whether it wants the latest snapshot or all history. Forgetting this decision produces silent data quality bugs — duplicate rows, empty columns, or misleading percentages — that look correct at the SQL level but break the user experience.

## Context

A labor market data warehouse ingested three vintages of OEWS wage data (2021, 2022, 2023) into the same fact table, distinguished by `source_release_id`. The web application had pages designed for single-vintage snapshots (occupation profiles, wage comparisons) and pages designed for multi-vintage analysis (trend explorer, ranked movers). Three separate bugs emerged from the same root cause: queries that did not specify their vintage policy.

## What Happened

1. **Snapshot page returned triple rows.** The wages comparison page (`/occupation/{soc}/wages`) showed 150 rows for 50 states instead of 50. The query had no `source_release_id` filter, so it returned one row per state per vintage (50 states x 3 vintages = 150 rows).

   ```sql
   -- BROKEN: returns all vintages
   SELECT g.geo_name, f.mean_annual_wage, ...
   FROM fact_occupation_employment_wages f
   JOIN dim_geography g ON f.geography_key = g.geography_key
   WHERE o.soc_code = '11-2021' AND g.geo_type = 'state'

   -- FIXED: latest vintage only
   SELECT g.geo_name, f.mean_annual_wage, ...
   WHERE ... AND f.source_release_id = '2023.05'
   ```

2. **Derived metrics showed N/A for every year.** The Trend Explorer displayed YoY Change and YoY % as N/A because the calculations only existed in `comparable` mode, while the UI defaulted to `as_published`. The data was present — the UI was pointing at the wrong comparability slice. The fix was changing the default `<select>` option from `as_published` to `comparable`.

3. **Percentages lacked absolute context.** The Ranked Movers page showed only YoY percent change without the absolute change, making it impossible to distinguish meaningful moves from noise. Athletes and Sports Competitors at +206% could mean anything without knowing the dollar amount (+$241,150). The fix was joining to `yoy_absolute_change` and displaying both columns.

4. **A vintage policy decision guide was codified.** Each page and endpoint was classified by its vintage intent:

   | Page / Endpoint | Vintage Policy | Filter |
   |---|---|---|
   | Occupation profile, wages comparison | Latest only | `source_release_id = MAX(...)` |
   | Trend Explorer, time-series API | All vintages | No filter (ordered by year) |
   | Ranked Movers | Latest derived only | Implicit (latest period in derived series) |
   | Geography comparison | Specific year (user-selected or latest) | `tp.year = ?` |

## Key Insights

- **Every multi-vintage query needs an explicit vintage policy.** Snapshot endpoints must filter to a specific `source_release_id`; only time-series endpoints should return multiple vintages. There is no safe default.
- **Derived metrics are tied to comparability mode.** When derived metrics only exist under a specific comparability mode, the UI must default to that mode. Otherwise users see empty columns and assume the feature is broken.
- **Percentages without absolute context are uninterpretable.** A +206% YoY change means nothing without knowing whether the absolute change is $241,150 or $150. Always pair percent change with the underlying absolute change.
- **The decision guide is a durable artifact.** Codifying vintage policy per endpoint prevents future pages from repeating the same mistakes. New endpoints should declare their vintage intent before writing the query.

## Related Lessons

- [Multi-Vintage Challenge](04-multi-vintage-challenge.md)
- [UI-Data Alignment](13-ui-data-alignment.md)
- [Derived Metrics from Base Observations](18-derived-metrics.md)
