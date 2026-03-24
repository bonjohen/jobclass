# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Labor market occupation data pipeline that ingests federal data products (SOC, OEWS, O*NET, Employment Projections) into a layered analytical warehouse. The core design principle: **occupation is the stable external key**; job titles, roles, and internal classifications map onto it, not the other way around.

The full design specification lives in `docs\specs\base_design_document.md`.
This was consolidated into 'docs\specs\project_detail_design.md'
This was used to construct two working documents:
* docs\specs\phased_release_plan.md
* docs\specs\test_plan.md

Implementation of the project follows the phased release of both design and test plans.

## Build Commands

```bash
# Install (editable mode for development)
pip install -e .

# Create or update the DuckDB schema
jobclass-pipeline migrate

# Run full pipeline: download all sources and load the warehouse
jobclass-pipeline run-all

# Check warehouse state (table row counts)
jobclass-pipeline status

# Start the web server on port 8000
jobclass-web                        # or: python -m jobclass.web.cli
jobclass-web --port 9000 --reload   # custom port + auto-reload

# Run all tests
pytest

# Unit tests only (fixture-based, no database needed)
pytest tests/unit/

# Web/API tests only (fixture-based, no database needed)
pytest tests/web/

# Real data validation tests (requires warehouse.duckdb)
pytest tests/warehouse/

# Linting (configured in pyproject.toml)
ruff check src/ tests/

# Build static site for GitHub Pages
MSYS_NO_PATHCONV=1 python scripts/build_static.py --base-path /jobclass

# Deploy static site to gh-pages branch
python scripts/deploy_pages.py
```

## Static Site / GitHub Pages

The site is published at **https://bonjohen.github.io/jobclass/**

- `scripts/build_static.py` pre-renders all HTML pages via the FastAPI TestClient and generates all API responses as static JSON files under `_site/`.
- A fetch shim is injected into each HTML page's `<head>`. It intercepts JavaScript `fetch()` calls to `/api/` and redirects them to the corresponding `.json` files.
- Search uses a client-side index built from the full occupation list in the database. The shim filters results locally, so no server-side search is needed.
- Wages endpoints map the `geo_type` query parameter to separate JSON files (e.g., `wages-national.json`, `wages-state.json`).
- Path rewriting handles the GitHub Pages subpath (`/jobclass`) for all links, assets, and API URLs.
- `scripts/deploy_pages.py` pushes `_site/` to the `gh-pages` branch via force-push.
- A `.nojekyll` file is included to prevent GitHub Pages Jekyll processing.

## Architecture: Four-Layer Warehouse

1. **Landing/Raw** — Immutable capture of downloaded artifacts. No business logic. Required metadata: file name, source URL, download timestamp, checksum, source release label, run ID.
2. **Standardized Staging** — Parse heterogeneous source files into relational structures. Standardized column names, explicit typing, explicit null semantics. No denormalization or semantic rollups.
3. **Core Warehouse** — Conformed dimensions (`dim_`), facts (`fact_`), and bridges (`bridge_`). Version-aware joins. No source-format assumptions.
4. **Marts** — Denormalized, query-friendly views for specific analytical questions. No new business logic that bypasses warehouse truth.

## Naming Conventions

- **Raw paths**: `raw/{source_name}/{dataset_name}/{source_release_id}/{run_id}/{original_file_name}`
- **Staging tables**: `stage__{source}__{dataset}` (e.g., `stage__bls__oews_state`, `stage__onet__skills`)
- **Core tables**: `dim_`, `fact_`, `bridge_` prefixes (e.g., `dim_occupation`, `fact_occupation_employment_wages`, `bridge_occupation_skill`)
- **Columns**: snake_case everywhere. Date-times in UTC. Versioned sources expose both `source_release_id` and `source_version`.

## Data Sources

| Source | Internal IDs | Role |
|--------|-------------|------|
| SOC | `soc_hierarchy`, `soc_definitions` | Occupation taxonomy backbone |
| OEWS | `oews_national`, `oews_state`, `oews_metro`, `oews_industry_national` | Employment counts and wage measures |
| O*NET | `onet_skills`, `onet_knowledge`, `onet_abilities`, `onet_tasks`, `onet_occupation_data` | Semantic descriptors (skills, tasks, etc.) |
| BLS Projections | `bls_employment_projections` | Forward-looking employment data |

## Key Design Decisions

- **Immutable raw storage**: Never overwrite downloaded artifacts. Reproducibility over storage savings.
- **Split semantic bridges**: O*NET domains get separate bridge tables (not a generic EAV table). More tables is acceptable for clarity.
- **Two time concepts**: Source release time (when published/captured) vs. business reference time (period described). Never conflate them.
- **As-published vs. comparable history**: These are separate analytical products. As-published preserves original taxonomy; comparable history uses crosswalk logic.
- **Idempotent loading**: Re-running the same dataset version must not create duplicates.
- **Fail-fast on schema drift**: Block warehouse publication until parser is updated or change is approved.
- **Preserve source nulls**: Never impute suppressed/missing OEWS values.

## Key Technical Notes

- **BLS blocks bare HTTP requests**: BLS.gov rejects requests without `Sec-Fetch-*` browser headers. The downloader (`src/jobclass/extract/download.py`) sends a full set of browser-like headers including `Sec-Fetch-Dest`, `Sec-Fetch-Mode`, `Sec-Fetch-Site`, and `Sec-Fetch-User`.
- **SOC 2018 XLSX format**: The SOC 2018 XLSX uses short group labels (`"Major"`, `"Minor"`, `"Broad"`, `"Detailed"`) while older CSV formats use full labels (`"Major Group"`, etc.). The SOC parser's `LEVEL_MAP` handles both.
- **OEWS XLSX columns are UPPERCASE**: BLS XLSX files use column names like `AREA`, `NAICS`, `OCC_CODE`. The OEWS parser normalizes via `_OEWS_COLUMN_ALIASES` to match the internal lowercase key convention.
- **BLS Projections employment is in thousands**: The XLSX source stores employment as thousands (e.g., 309.4 = 309,400). The projections parser converts to whole numbers.
- **5 NEM 2024 occupation codes don't map to SOC 2018**: This is an expected gap. The National Employment Matrix uses some codes not present in the SOC 2018 taxonomy. The projections loader performs an inner join against `dim_occupation`, so these rows are silently excluded.
- **Military occupations (SOC 55-xxxx) have no data**: Military occupations exist in the SOC taxonomy but have no OEWS wages, O*NET descriptors, or BLS projections data in any source.

## Pipeline Flow

Extract (declarative, manifest-driven) -> Parse (dataset-specific) -> Validate (structural, semantic, temporal, drift) -> Load (idempotent at dataset-version grain)

Logical pipelines: `taxonomy_refresh`, `oews_refresh`, `onet_refresh`, `projections_refresh`, `warehouse_publish`. SOC must complete before occupation conformance; OEWS and O*NET may run independently.

## Testing Strategy

- **507+ tests** across three test directories:
  - `tests/unit/` — Fixture-based parser, loader, orchestration, validation, and config tests. No database or network needed.
  - `tests/web/` — FastAPI TestClient tests for all API endpoints, HTML pages, security headers, accessibility, and end-to-end smoke tests. No database needed (uses in-memory fixtures).
  - `tests/warehouse/` — Real data validation tests against `warehouse.duckdb`. **Automatically skipped** if the warehouse file is absent. Run `jobclass-pipeline run-all` first to populate it.
- Parser unit tests on representative source files
- Schema contract tests (fail on missing/changed columns)
- Grain uniqueness tests (fail on duplicate business keys)
- Referential integrity tests (facts/bridges must point to existing dimensions)
- Historical regression tests against known published totals
- Idempotent rerun tests (no duplicate output on re-run)

## Release 1 Scope

In scope: SOC hierarchy, OEWS national + state, O*NET core descriptors, warehouse schema with lineage/version tracking, repeatable orchestration, validation, and five initial marts (`occupation_summary`, `occupation_wages_by_geography`, `occupation_skill_profile`, `occupation_task_profile`, `occupation_similarity_seeded`).

Not in scope: HR job architecture, title normalization, international harmonization, real-time APIs.
