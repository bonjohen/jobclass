# The Federal Labor Data Landscape

## The Lesson

When building an analytical warehouse from multiple federal data products, the single most important architectural decision is identifying the stable external key that connects them. For labor data, that key is the Standard Occupational Classification (SOC) code — every design decision flows from treating occupation as the backbone, not as one attribute among many.

## Context

The JobClass project ingests four federal data products — SOC taxonomy, OEWS employment/wage surveys, O*NET occupational descriptors, and BLS Employment Projections — into a layered DuckDB warehouse. Each product is published by a different office on a different schedule in a different format, but they all describe the same ~870 occupations using the same SOC code system. The challenge was designing a warehouse that treats these as four views of one reality rather than four independent datasets.

## What Happened

1. **The SOC taxonomy was identified as the backbone.** The Standard Occupational Classification assigns hierarchical codes (e.g., `11-1011` for Chief Executives, where `11` is the Management major group and `1011` narrows to the specific occupation). SOC 2018 defines roughly 870 detailed occupations and is updated approximately every 10 years.
2. **Four data products were mapped to a single key.** OEWS provides employment counts and wage statistics by occupation and geography (annual, May reference period). O*NET provides skills, knowledge, abilities, and tasks (continuously versioned). BLS Projections provide 10-year employment outlook (biennial). All three join to the SOC taxonomy through occupation codes.
3. **The SOC dimension was loaded first in every pipeline run.** Because every other data product joins to `dim_occupation` through the SOC code, the taxonomy must be present before any facts can be conformed. The orchestrator enforces this ordering.
4. **Unmappable codes were handled by exclusion.** Approximately 5 National Employment Matrix 2024 codes have no corresponding SOC 2018 entry. The projections loader performs an inner join against `dim_occupation`, silently excluding these rows — an expected and documented gap.

## Key Insights

- **Four datasets, one key.** SOC, OEWS, O*NET, and Projections are not independent datasets — they are four views of the same occupational reality connected by the SOC code. Designing the warehouse around this fact is what makes cross-domain queries possible.
- **Taxonomy load order is a hard dependency.** Every fact and bridge table references `dim_occupation`. If the SOC taxonomy hasn't loaded, dimension key lookups fail silently or produce orphaned rows. The pipeline enforces SOC-first ordering.
- **Taxonomy changes break naive time-series.** When the SOC taxonomy updates (roughly every decade), codes can split, merge, or disappear. Any system that assumes occupation codes are permanent will produce incorrect comparisons across taxonomy versions.
- **Exclusion is safer than imputation for unmappable codes.** The ~5 NEM 2024 codes that don't exist in SOC 2018 are silently dropped via inner join rather than force-mapped. This preserves data integrity at the cost of minor coverage gaps.

## Related Lessons

- [The Multi-Vintage Challenge](04-multi-vintage-challenge.md) — how taxonomy changes interact with multi-year analysis
- [Crosswalk and Taxonomy Evolution](16-taxonomy-evolution.md) — deeper treatment of SOC version transitions
- [Dimensional Modeling for Labor Data](03-dimensional-modeling.md) — the warehouse architecture that implements these connections
