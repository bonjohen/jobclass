# JobClass — Labor Market Occupation Pipeline

A data pipeline that ingests federal labor market data products into a layered analytical warehouse, with occupation as the stable external key.

## What It Does

Ingests, validates, and models data from four federal sources into a queryable warehouse:

- **SOC** — Occupation taxonomy and hierarchy
- **OEWS** — Employment counts and wage distributions by occupation and geography
- **O\*NET** — Semantic descriptors (skills, knowledge, abilities, tasks) tied to occupations
- **Employment Projections** — Forward-looking employment outlook by occupation

## Questions It Answers

- How many people work in a given occupation, nationally and by state?
- What are the wage distributions across geographies?
- What skills, tasks, knowledge, and abilities define an occupation?
- Which occupations are similar based on shared descriptors?
- What is the projected employment outlook for an occupation?
- What source version and release lineage produced a given result?

## Architecture

Four-layer warehouse: **Raw** (immutable source capture) → **Staging** (parsed, typed, standardized) → **Core** (conformed dimensions, facts, bridges) → **Marts** (analyst-ready denormalized views).

Key properties: idempotent loading, version-aware modeling, immutable raw storage, fail-fast on schema drift, explicit source lineage on every record.

## Phase Commit Log

Status of each phase's commit upon completion.

| Phase | Description | Commit Message | Status |
|-------|-------------|----------------|--------|
| 1 | Project Foundation | Phase 1: Project foundation — structure, config, database, logging, tests | Complete |
| 2 | Extraction Framework & Run Manifest | Phase 2: Extraction framework, source manifest, run manifest, and tests | Complete |
| 3 | SOC Taxonomy Pipeline | Phase 3: SOC taxonomy pipeline — parser, staging, dim_occupation, bridge, validations | Complete |
| 4 | OEWS Employment & Wages Pipeline | Phase 4: OEWS pipeline — parser, staging, dim_geography, dim_industry, fact table, validations | Complete |
| 5 | O*NET Semantic Pipeline | Phase 5: O*NET pipeline — parsers, staging, dim_skill/knowledge/ability/task, bridges, validations | Complete |
| 6 | Validation Framework & Failure Handling | Phase 6: Validation framework — structural, grain, ref integrity, temporal, drift, failure modes | Complete |
| 7 | Observability & Run Reporting | Phase 7: Observability — reporters, run inspection, row-count deltas, reconciliation | Complete |
| 8 | Orchestration | Phase 8: Orchestration — pipelines, dependency enforcement, publish gating, idempotence | Complete |
| 9 | Analyst Marts | Phase 9: Analyst marts — 5 views, Jaccard similarity, query tests, publish gating | Complete |
| 10 | Employment Projections (Optional R1) | | Pending |
| 11 | End-to-End Integration & Deliverables | | Pending |

## Project Structure

```
src/jobclass/          # Main package
  config/              # Settings, database connection, migrations
  extract/             # Download, manifest reader, storage, version detection
  parse/               # Source-specific parsers (SOC, OEWS, O*NET)
  load/                # Staging and warehouse loaders
  validate/            # Structural, semantic, temporal validations
  observe/             # Logging, run manifest operations
  orchestrate/         # Pipeline orchestration
  marts/               # Analyst-facing mart view helpers
  utils/               # Path builder, shared utilities
tests/                 # pytest suite (unit + integration)
  fixtures/            # Sample source files for parser tests
migrations/            # SQL schema migrations (DuckDB)
config/                # Source manifest (YAML)
docs/specs/            # Design docs, release plan, test plan
```

## Documentation

| Document | Purpose |
|----------|---------|
| [Design Document](docs/specs/base_design_document.md) | Full architectural specification, data model, pipeline flow, and design tradeoffs |
| [Project Detail Design](docs/specs/project_detail_design.md) | Requirements from the perspective of downstream users; input for release and test planning |
| [Phased Release Plan](docs/specs/phased_release_plan.md) | Task-level tracking with status, timestamps, and requirement traceability |
| [Test Plan](docs/specs/test_plan.md) | 167 tests across 12 types, aligned phase-by-phase with the release plan |

## Status

Implementation in progress. Phases 1–9 complete. Currently working through Phase 10 (employment projections).
