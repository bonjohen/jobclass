# JobClass — Labor market occupation data pipeline

Ingests federal labor market data (SOC, OEWS, O*NET, BLS Projections) into a four-layer DuckDB warehouse and serves it through a FastAPI web UI.

**Live site:** https://bonjohen.github.io/jobclass/

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
| **O\*NET** | Skills, knowledge, abilities, and tasks tied to each occupation |
| **BLS Employment Projections** | Forward-looking employment outlook by occupation |

## Architecture

Four-layer warehouse:

1. **Raw** — Immutable capture of downloaded source files. No transformation.
2. **Staging** — Parsed into relational tables with standardized column names and explicit typing.
3. **Core** — Conformed dimensions (`dim_`), facts (`fact_`), and bridges (`bridge_`) with version-aware joins.
4. **Marts** — Denormalized, query-ready views for analytical use.

The pipeline is idempotent: re-running the same source version produces no duplicates. Schema drift is detected and blocks publication until resolved.

**Web layer:** FastAPI serves HTML pages (search, occupation profiles, wage comparison, skill/task views, projections) plus JSON APIs. A static site generator produces the GitHub Pages deployment.

## Project structure

```
src/jobclass/
  config/        Settings, database, migrations
  extract/       Download, manifest, storage, version detection
  parse/         Source-specific parsers (SOC, OEWS, O*NET, Projections)
  load/          Staging and warehouse loaders
  validate/      Structural, semantic, temporal, drift validations
  observe/       Logging, run manifest
  orchestrate/   Pipeline orchestration
  marts/         Analyst-facing mart views
  web/           FastAPI app, templates, static assets
tests/           pytest suite (unit + integration)
migrations/      SQL schema migrations (DuckDB)
config/          Source manifest (YAML)
scripts/         Static site build and deploy
```

## Testing

```bash
# Full suite (484+ tests)
pytest

# Warehouse-only tests (real data validation)
pytest tests/warehouse/
```

Tests cover parsers, schema contracts, grain uniqueness, referential integrity, temporal consistency, idempotence, regression against known totals, API correctness, accessibility, and E2E smoke tests.

## Static site deployment

```bash
python scripts/build_static.py --base-path /jobclass
python scripts/deploy_pages.py
```

## CLI reference

```bash
# Pipeline
jobclass-pipeline migrate       # Run database migrations
jobclass-pipeline status        # Check migration and database status
jobclass-pipeline run-all       # Run all pipelines

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

Health check: `GET /api/health` | Readiness: `GET /api/ready` | Metrics: `GET /metrics`

## License

See LICENSE.
