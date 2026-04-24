# JobClass — Labor market occupation data pipeline

Ingests federal labor market data (SOC, OEWS, O*NET, BLS Projections) into a four-layer DuckDB warehouse and serves it through a FastAPI web UI.

**Live site:** https://jobclass.johnboen.com/

## Quick start

**Prerequisites:** Python 3.12+, pip

```bash
git clone <repo-url> && cd jobclass
pip install -e .

# Build the warehouse (~50 MB download from BLS/O*NET, takes ~10 min)
jobclass-pipeline migrate
jobclass-pipeline run-all

# Start the web server
jobclass-web
# Open http://127.0.0.1:8000
```

## Data sources

| Source | What it provides |
|--------|-----------------|
| **SOC** (Standard Occupational Classification) | Occupation taxonomy and hierarchy — the backbone for all joins |
| **OEWS** (Occupational Employment & Wage Statistics) | Employment counts and wage distributions by occupation and geography |
| **O\*NET** | Skills, knowledge, abilities, work activities, education, technology, and tasks tied to each occupation |
| **BLS Employment Projections** | Forward-looking employment outlook by occupation |
| **BLS CPI-U** | Consumer price index for inflation-adjusted (real) wage metrics. Full CPI domain: item hierarchy, geographic areas, series metadata, current observations, relative importance weights, average prices |
| **SOC Crosswalk** | SOC 2010↔2018 occupation code mappings for historical depth |

## Architecture

Four-layer warehouse:

1. **Raw** — Immutable capture of downloaded source files. No transformation.
2. **Staging** — Parsed into relational tables with standardized column names and explicit typing.
3. **Core** — Conformed dimensions (`dim_`), facts (`fact_`), and bridges (`bridge_`) with version-aware joins.
4. **Marts** — Denormalized, query-ready views for analytical use.

The pipeline is idempotent: re-running the same source version produces no duplicates. Schema drift is detected and blocks publication until resolved.

**Web layer:** FastAPI serves HTML pages (search, hierarchy browser, occupation profiles, wage comparison, skill/task views, projections, trend explorer, occupation comparison, geography comparison, ranked movers, CPI explorer, Pipeline Explorer, 20 lesson pages) plus JSON APIs backed by 9 API routers. A static site generator produces the GitHub Pages deployment with a client-side fetch shim for API interception.

## Project structure

```
src/jobclass/
  config/        Settings, database, migrations
  extract/       Download, manifest, storage, version detection
  parse/         Source-specific parsers (SOC, OEWS, O*NET, Projections, CPI)
  load/          Staging and warehouse loaders
  validate/      Structural, semantic, temporal, drift validations
  observe/       Logging, run manifest
  orchestrate/   Pipeline orchestration (9 pipelines)
  marts/         Analyst-facing mart views
  utils/         Path resolution utilities
  web/
    app.py       FastAPI app factory + 18 page routes
    lessons.py   20-lesson registry (metadata)
    api/         9 API routers (occupations, wages, skills, projections,
                   trends, cpi, health, metrics, methodology)
    templates/   Jinja2 HTML templates
    static/      CSS and JavaScript assets
tests/           pytest suite (unit, web, warehouse, integration)
migrations/      SQL schema migrations (DuckDB)
config/          Source manifest (YAML)
scripts/         Static site build and deploy
```

## Time-series labor intelligence

The warehouse extends point-in-time occupation reporting with time-series analysis:

- **Conformed metric catalog** (`dim_metric`) — 6 base metrics + 7 derived metrics with units, display format, comparability constraints
- **Time-period dimension** (`dim_time_period`) — annual periods auto-populated from warehouse fact years
- **Multi-vintage OEWS** — pipeline downloads and loads 3 years of OEWS data (2021–2023) for true multi-year time-series
- **Observation fact** (`fact_time_series_observation`) — normalized from OEWS and projections at the grain of metric + occupation + geography + period + source release + comparability mode
- **Derived-series fact** (`fact_derived_series`) — year-over-year change, percent change, 3-year rolling average, state-vs-national gap, rank delta, real (inflation-adjusted) wages
- **Comparable history** — as-published vs. comparable-history modes; projection metrics excluded from comparable series
- **5 time-series marts** — trend series, geography gap, rank change, projection context, similarity trend overlay

```bash
# Run time-series pipeline standalone
jobclass-pipeline timeseries-refresh
```

## Testing

```bash
# Full suite (840+ tests)
pytest

# Warehouse-only tests (real data validation)
pytest tests/warehouse/
```

Tests cover parsers, schema contracts, grain uniqueness, referential integrity, temporal consistency, idempotence, regression against known totals, API correctness, input validation, security headers, accessibility, lessons section, trends/time-series, and E2E smoke tests.

## Static site deployment

```bash
MSYS_NO_PATHCONV=1 python scripts/build_static.py --base-path /
python scripts/deploy_pages.py
```

## Pipelines

`run-all` executes these pipelines in dependency order:

| Pipeline | Purpose | Depends on |
|----------|---------|------------|
| `taxonomy_refresh` | SOC hierarchy and definitions → `dim_occupation` | — |
| `oews_refresh` | OEWS employment/wages → `dim_geography`, facts | taxonomy |
| `onet_refresh` | O\*NET descriptors → skill/knowledge/ability dims + bridges | taxonomy |
| `projections_refresh` | BLS employment projections → projection facts | taxonomy |
| `cpi_refresh` | CPI-U single series → `dim_price_index`, price facts | — |
| `cpi_domain_refresh` | Full CPI domain → member/area/series dims, observations, weights, prices | — |
| `crosswalk_refresh` | SOC 2010↔2018 → `bridge_soc_crosswalk` | — |
| `warehouse_publish` | Referential integrity gate → mart views | all above |
| `timeseries_refresh` | Build time-series observations and derived metrics | warehouse_publish |

## Database schema

The warehouse contains **57+ tables** across the four layers:

- **15 dimensions** — `dim_occupation`, `dim_geography`, `dim_industry`, `dim_skill`, `dim_knowledge`, `dim_ability`, `dim_task`, `dim_work_activity`, `dim_technology`, `dim_education_requirement`, `dim_cpi_member`, `dim_cpi_area`, `dim_cpi_series_variant`, `dim_time_period`, `dim_metric`
- **8 facts** — employment/wages, projections, time-series observations, derived series, CPI observations, relative importance, average prices, revision vintages
- **12 bridges** — occupation-to-descriptor bridges (skill, knowledge, ability, task, work activity, technology, education), SOC hierarchy, SOC crosswalk, CPI member/area hierarchies
- **17 staging tables** — one per parsed dataset

## CLI reference

```bash
# Pipeline
jobclass-pipeline migrate              # Run database migrations
jobclass-pipeline status               # Check migration and database status
jobclass-pipeline run-all              # Run all pipelines
jobclass-pipeline timeseries-refresh   # Run time-series pipeline only

# Web server
jobclass-web                            # Default: http://127.0.0.1:8000
jobclass-web --host 0.0.0.0 --port 8080 --reload   # Custom host/port
```

| Environment variable | Default | Description |
|---------------------|---------|-------------|
| `JOBCLASS_DB_PATH` | `warehouse.duckdb` | Path to the DuckDB database file |

## Container deployment

```bash
docker build -t jobclass .
docker run -p 8000:8000 -v ./warehouse.duckdb:/app/warehouse.duckdb:ro jobclass
```

Health check: `GET /api/health` | Metrics: `GET /metrics`

## Release notes

### NDS6-7 — CPI Inflation, SOC Crosswalk, Extended Test Coverage (2026-03-24)

- **BLS CPI-U integration**: Parser, loader, and pipeline for Consumer Price Index data. Real (inflation-adjusted) mean and median wage metrics computed via CPI-U deflation (base year 2023).
- **SOC 2010↔2018 crosswalk**: Parser auto-classifies mapping types (1:1, split, merge, complex) by cardinality. Bridge table and pipeline wired into `run-all`. Foundation for extending comparable history to pre-2018 OEWS vintages.
- **Real wage UI**: Trend Explorer and Ranked Movers dropdowns include Real Mean/Median Annual Wage options. Static site generator produces per-occupation real wage JSON files.
- **Extended test coverage**: 653 tests (+37). New: CPI parser/loader/deflation tests (16), crosswalk parser/loader tests (13), ranked movers year filter tests (7), comparison endpoint edge cases (8), Pydantic contract validation (7), real wage UI tests (2).

### NDS3-5 — Work Activities, Education, Technology Skills (2026-03-24)

- **O\*NET Work Activities**: Reuses generic descriptor pipeline. New API endpoint, occupation profile section, and 8 tests.
- **O\*NET Education & Training**: Custom parser for category-based schema. Education summary with highest-percentage level labels. 9 tests.
- **O\*NET Technology Skills**: Custom parser for commodity-based schema. Tools/Technology grouping with Hot Technology badges. 9 tests.

### NDS0-2 — Code Quality Prep, Knowledge, Abilities (2026-03-24)

- Centralized `fetchWithTimeout` and lesson slug registry. Fixed `_table_exists`, drift thresholds, deploy sanity checks.
- Surfaced O\*NET Knowledge and Abilities on occupation profiles (zero new downloads — data already in warehouse).
- Added `response_model=` to all trends API endpoints. Fixed `TrendPoint.suppressed` type.

## License

See LICENSE.
