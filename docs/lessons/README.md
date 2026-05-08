# Lessons Learned

Patterns, mistakes, and decisions extracted from the JobClass project. Each lesson is standalone and designed to be useful on any project.

## Data Engineering

- [02 — The Federal Labor Data Landscape](02-federal-data-landscape.md) — Four federal data products connected by a single occupation code
- [05 — Data Quality Traps in Government Sources](05-data-quality-traps.md) — Suppressed values, format shifts, and silent schema changes
- [14 — Schema Drift Detection](14-schema-drift.md) — Automated guards against upstream format changes
- [15 — Inflation Adjustment with CPI](15-inflation-adjustment.md) — CPI-U deflation to convert nominal wages to real dollars
- [17 — Extract Patterns for Government APIs](17-government-apis.md) — Browser headers, retry logic, and manifest-driven downloads

## Architecture

- [01 — Design System Cross-Pollination](01-design-system-cross-pollination.md) — Porting visual feel between projects via design tokens
- [03 — Dimensional Modeling for Labor Data](03-dimensional-modeling.md) — Four-layer warehouse with conformed dimensions and explicit grain
- [04 — The Multi-Vintage Challenge](04-multi-vintage-challenge.md) — Comparing data across survey years without mixing vintages
- [07 — Idempotent Pipeline Design](07-idempotent-pipelines.md) — Delete-before-insert, manifest dedup, and version-aware loading
- [16 — Taxonomy Evolution](16-taxonomy-evolution.md) — SOC crosswalks, code reclassification, and comparable history

## Web / Static

- [08 — Static Site Generation](08-static-site-generation.md) — Pre-rendering a FastAPI app to static HTML + JSON for GitHub Pages
- [13 — UI-Data Alignment](13-ui-data-alignment.md) — Keeping frontend labels, dropdowns, and charts consistent with API contracts
- [20 — Geography Comparison Pitfalls](20-geography-pitfalls.md) — Gaps, cost-of-living, and suppression in state-level wage data
- [21 — Fetch Shim Architecture](21-fetch-shim.md) — Monkey-patching fetch() to serve static JSON as a fake API

## Testing

- [09 — Testing and Deployment](09-testing-deployment.md) — Three test directories, CI matrix, and static site deployment
- [10 — Choosing the Right Similarity Algorithm](10-similarity-algorithms.md) — Why Jaccard fails on O*NET skills and cosine similarity works
- [11 — Thread-Safe Database Connections](11-thread-safety.md) — Per-request DuckDB connections for concurrent web requests
- [12 — Multi-Vintage Query Pitfalls](12-multi-vintage-queries.md) — Filtering by vintage, latest-only views, and cross-vintage joins

## Pipeline

- [06 — Time-Series Normalization](06-time-series-normalization.md) — Metric catalog, observation facts, and derived series
- [18 — Derived Metrics from Base Observations](18-derived-metrics.md) — YoY change, rolling averages, and idempotent derivation
- [19 — Ranked Movers and Outlier Interpretation](19-outlier-interpretation.md) — Small-denominator volatility and absolute vs. percentage change
