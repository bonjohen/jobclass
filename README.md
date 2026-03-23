# JobClass — Labor Market Occupation Pipeline

![CI](https://github.com/YOUR_ORG/jobclass/actions/workflows/ci.yml/badge.svg)

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
| 10 | Employment Projections (Optional R1) | Phase 10: Employment Projections — parser, staging, fact, validations, pipeline | Complete |
| 11 | End-to-End Integration & Deliverables | Phase 11: E2E integration, schema docs, sample queries, deliverable verification | Complete |
| W1 | Website: Project Setup & API Foundation | Phase W1: FastAPI app, health/metadata APIs, base layout, CSS, test framework | Complete |
| W2 | Website: Occupation Search & Hierarchy | Phase W2: Search, hierarchy, profile APIs, search/hierarchy/profile pages, 16 tests | Complete |
| W3 | Website: Employment & Wages Display | Phase W3: Wages API, geography API, state comparison page, suppression handling, 13 tests | Complete |
| W4 | Website: Skills & Tasks Display | Phase W4: Skills, tasks, similarity APIs with O*NET lineage, 13 tests | Complete |
| W5 | Website: Trends & Projections Display | Phase W5: Projections API with education/training, profile integration, 9 tests | Complete |
| W6 | Website: Landing Page & Navigation | Phase W6: Stats API, landing spotlight, methodology page, navigation, 14 tests | Complete |
| W7 | Website: Methodology & Data Transparency | Phase W7: Sources API, validation API, methodology page with live status, 14 tests | Complete |
| W8 | Website: Visual Polish & Responsive Design | Phase W8: Responsive CSS, accessibility (ARIA, skip-nav, focus), performance checks, 14 tests | Complete |
| W9 | Website: End-to-End Integration & Deployment | Phase W9: E2E smoke tests, worked example, lineage verification, full suite 376 tests | Complete |

## CLI Usage

Install the package in development mode:

```bash
pip install -e ".[dev]"
```

### Pipeline CLI

```bash
# Run database migrations
jobclass-pipeline migrate

# Check migration and database status
jobclass-pipeline status
```

### Web Server CLI

```bash
# Start the web server (default: http://127.0.0.1:8000)
jobclass-web

# Custom host/port with auto-reload for development
jobclass-web --host 0.0.0.0 --port 8080 --reload
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JOBCLASS_DB_PATH` | `warehouse.duckdb` | Path to the DuckDB database file |

## Container

```bash
# Build
docker build -t jobclass .

# Run (mount your warehouse database)
docker run -p 8000:8000 -v ./warehouse.duckdb:/app/warehouse.duckdb:ro jobclass

# Or use docker-compose
docker-compose up
```

The container runs the web server on port 8000 with a built-in health check at `/api/health`.

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

All 11 pipeline phases and 9 website phases complete. 376 tests passing — 243 pipeline tests (unit, integration, contract, grain, referential integrity, semantic, temporal, drift, idempotence, regression, failure-mode, query validation) and 133 web tests (API, page rendering, accessibility, E2E smoke).
