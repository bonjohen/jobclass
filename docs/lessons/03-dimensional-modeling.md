# Dimensional Modeling for Labor Data

## The Lesson

A four-layer warehouse architecture (raw, staging, core, marts) with strict separation of concerns at each layer produces a system where raw data is always recoverable, business meaning is assigned in exactly one place, and analytical queries never need to understand source formats.

## Context

The JobClass project ingests federal labor data from multiple publishers (BLS, DOL, O*NET Center) in heterogeneous formats (XLSX, CSV, ZIP archives). Each source has its own column naming conventions, update cadences, and null semantics. The warehouse needed to conform these into a single queryable schema while preserving full lineage back to the original downloaded files.

## What Happened

1. **The raw/landing layer was designed as immutable storage.** Every downloaded file is stored exactly as received with metadata: URL, download timestamp, SHA-256 checksum, source release label, and run ID. Files are never overwritten. This guarantees reproducibility — if anything goes wrong downstream, reprocessing starts from the original artifact.
2. **The staging layer parsed raw files into relational tables.** Each source gets its own staging table (e.g., `stage__bls__oews_national`). Column names are standardized to `snake_case`, types are made explicit, and null semantics are preserved. No business interpretation happens here — only structural normalization.
3. **The core warehouse layer conformed staged data into shared dimensions and facts.** Dimension tables (`dim_occupation`, `dim_geography`, `dim_industry`) store descriptive attributes with surrogate integer keys. Fact tables (`fact_occupation_employment_wages`) store measurements keyed to dimensions. Bridge tables (`bridge_occupation_skill`) resolve many-to-many relationships.
4. **Dimension tables were designed for key stability.** A dimension like `dim_geography` stores the business key (`geo_type + geo_code`), descriptive attributes (`name`, `current version flag`), and a surrogate key. Facts reference only the surrogate key, so geographic names can change without rewriting fact history.
5. **Every fact table was given an explicit grain.** The grain of `fact_occupation_employment_wages` is `(reference_period, geography_key, industry_key, ownership_code, occupation_key, source_dataset)`. Duplicating this grain triggers a constraint violation — the database itself enforces no-duplicate facts.
6. **Bridge tables were kept domain-specific.** Each O*NET domain (skills, knowledge, abilities, tasks) gets its own bridge table rather than sharing a generic entity-attribute-value table. More tables is the explicit trade-off for self-documenting schema.
7. **Analyst marts were built as denormalized views.** Pre-joined views like `occupation_summary` combine occupation, wages, and skills into single queryable structures. Marts contain no new business logic — they only reshape what the core warehouse already established.

## Key Insights

- **Immutable raw storage is the cheapest insurance.** Never modifying downloaded artifacts means any downstream bug can be fixed by reprocessing from raw. Storage is cheap; re-downloading from government servers that may change or disappear is not.
- **Surrogate keys decouple facts from dimension changes.** By storing only integer keys in fact tables, dimension attributes (names, labels, hierarchies) can evolve without rewriting historical facts. This is especially valuable for geographic and occupational dimensions that periodically get renamed or reclassified.
- **The grain rule catches loader bugs.** Defining a unique constraint on the fact table's grain columns is both documentation (what makes a row unique) and enforcement (the database rejects duplicates). Every loader bug that produces duplicate facts is caught at insert time rather than discovered during analysis.
- **Domain-specific bridges beat generic EAV.** A `bridge_occupation_skill` table with typed columns is immediately understandable; a generic `bridge_occupation_attribute(domain, element_id, value)` table requires documentation to interpret. The cost is more DDL; the benefit is a self-documenting schema.

## Related Lessons

- [The Federal Labor Data Landscape](02-federal-data-landscape.md) — the data sources that feed this dimensional model
- [Idempotent Pipeline Design](07-idempotent-pipelines.md) — the loading patterns that maintain grain integrity
- [The Multi-Vintage Challenge](04-multi-vintage-challenge.md) — how dimension deduplication enables cross-vintage analysis
