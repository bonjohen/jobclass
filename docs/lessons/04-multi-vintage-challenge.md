# The Multi-Vintage Challenge

## The Lesson

When loading multiple vintages of the same dataset, dimension tables must deduplicate on business key alone — not on business key plus source release. Including the source release in dimension lookups gives the same real-world entity different surrogate keys in each vintage, making cross-vintage joins return zero rows.

## Context

The JobClass warehouse loads three vintages of the OEWS survey (2021, 2022, 2023), each a complete employment-and-wage snapshot with a May reference period. To answer trend questions like "how has employment for Chief Executives changed from 2021 to 2023?", facts from different vintages must join through shared dimension keys. The initial implementation gave each vintage its own dimension rows, silently breaking every cross-vintage query.

## What Happened

1. **Three OEWS vintages were added to the source manifest.** The manifest uses suffix-based naming: `oews_national_2021`, `oews_national_2022`, `oews_national_2023`. The orchestrator pairs national and state entries by matching suffixes (`oews_national_2021` pairs with `oews_state_2021`).
2. **The naive dimension loader included `source_release_id` in lookups.** The geography dimension lookup query was `WHERE geo_type = ? AND geo_code = ? AND source_release_id = ?`. Since each vintage has a different release ID, "National" got geography key 1 from OEWS 2021, key 2 from 2022, and key 3 from 2023.
3. **Cross-vintage joins returned zero rows.** Attempting to compute year-over-year employment change required joining 2021 and 2023 facts on geography. Different surrogate keys for the same physical area meant the join predicate never matched.
4. **The fix was a single predicate change.** Removing `source_release_id` from the geography lookup (`WHERE geo_type = ? AND geo_code = ?`) caused the loader to find and reuse the existing surrogate key. North Carolina gets one geography key regardless of which vintage loaded it.
5. **The same principle was applied to all stable dimensions.** Geography, industry, and occupation dimensions all use business-key-only lookups. Dimensions that genuinely change between releases (like occupation definitions across SOC taxonomy versions) are handled separately through version-aware logic.

### Before (broken)

```sql
WHERE geo_type = ? AND geo_code = ? AND source_release_id = ?
```

### After (correct)

```sql
WHERE geo_type = ? AND geo_code = ?
```

## Key Insights

- **Per-vintage dimension keys make cross-vintage analysis impossible.** The same real-world entity getting different surrogate keys in each vintage means no join predicate can connect them. This is the most common structural bug in multi-vintage warehouses.
- **The fix is smaller than the bug.** Removing one predicate from a WHERE clause — `AND source_release_id = ?` — is what made the entire time-series analysis layer possible. The simplicity of the fix belies its architectural importance.
- **Suffix-based naming is a simple, extensible convention.** Using `oews_national_2021` / `oews_state_2021` with suffix matching to pair related datasets is easy to debug, easy to extend with new vintages, and requires no metadata tables.
- **Not all dimensions are stable across vintages.** Geography doesn't change between OEWS releases, but occupation definitions do change across SOC taxonomy versions. The deduplication strategy must distinguish between dimensions that are genuinely version-independent and those that carry version-specific meaning.

## Related Lessons

- [Dimensional Modeling for Labor Data](03-dimensional-modeling.md) — the warehouse architecture that dimension deduplication operates within
- [Time-Series Normalization](06-time-series-normalization.md) — the analytical layer built on top of cross-vintage joins
- [Multi-Vintage Queries](12-multi-vintage-queries.md) — query patterns for working with conformed multi-vintage data
- [Taxonomy Evolution](16-taxonomy-evolution.md) — handling dimensions that genuinely do change between versions
