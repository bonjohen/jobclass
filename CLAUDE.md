# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Labor market occupation data pipeline that ingests federal data products (SOC, OEWS, O*NET, Employment Projections) into a layered analytical warehouse. The core design principle: **occupation is the stable external key**; job titles, roles, and internal classifications map onto it, not the other way around.

The full design specification lives in `docs\specs\base_design_document.md`.
This was consolidated into `docs\specs\project_detail_design.md`.
This was used to construct two working documents:
* `docs\specs\phased_release_plan.md` — **Complete** (all tasks done)
* `docs\specs\test_plan.md`

Subsequent release plans (all complete):
* `docs\specs\time_series_labor_plan.md` — Time-series intelligence pipeline (101/101 tasks)
* `docs\specs\lessons_release_plan.md` — Lessons section with 12 educational pages (36/36 tasks)

Active release plans:
(none)

Completed release plans:
* `docs\specs\pipeline_explorer_plan.md` — Pipeline Explorer interactive visualization (140/140 tasks, PE0–PE13)
* `docs\specs\new_data_source_plan.md` — 7 new data sources, 102 tasks across 8 phases (NDS1–NDS8)
* `docs\specs\phased_code_review_release_plan_v2.md` — 18 findings, 62 tasks across 4 phases (CR2-P1–P4)

Design documents:
* `docs\specs\pipeline_explorer_design.md` — Pipeline Explorer design requirements and experience concept
* `docs\specs\new_data_source_design.md` — Detailed design for all 7 new data sources
* `docs\specs\code_review_plan_v2.md` — Full V2 code review findings and remediation plan
* `docs\specs\code_review_agent_v2.md` — V2 review prompt

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
- Path rewriting handles the GitHub Pages subpath (`/jobclass`) for all links, assets, and API URLs.
- `scripts/deploy_pages.py` pushes `_site/` to the `gh-pages` branch via force-push.
- A `.nojekyll` file is included to prevent GitHub Pages Jekyll processing.

### Shim URL Pattern → JSON File Mapping

| API URL Pattern | Static JSON File | Notes |
|----------------|-----------------|-------|
| `/api/occupations/search?q=...` | `/api/occupations/search.json` | Client-side filtering from full index |
| `/api/occupations/{soc}/wages?geo_type=X` | `/api/occupations/{soc}/wages-X.json` | Separate file per geo_type |
| `/api/trends/movers?year=Y` | `/api/trends/movers-Y.json` | Per-year file; default loads `movers.json` |
| `/api/trends/{soc}?metric=M` | `/api/trends/{soc}-M.json` | Per-metric file; default loads `{soc}.json` |
| `/api/trends/compare/occupations?codes=...` | Client-side composition | Fetches per-occupation trend + detail JSONs |
| `/api/trends/compare/geography?soc_code=X` | `/api/trends/compare/geography-X.json` | Per-occupation file |

### Cache-Busting Convention

Static assets in `base.html` use a version query parameter: `main.css?v=CR4`, `main.js?v=CR4`. **Bump the `?v=` value whenever CSS or JS files change.** Use a short tag (e.g., `NDS1`, `CR5`) referencing the change that triggered the update.

### Local Testing

```bash
# Build the static site
MSYS_NO_PATHCONV=1 python scripts/build_static.py --base-path /jobclass

# Serve locally (Python built-in server)
cd _site && python -m http.server 8080
# Open http://localhost:8080/jobclass/
```

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
| BLS CPI-U | `bls_cpi` | Consumer price index for inflation adjustment |
| SOC Crosswalk | `soc_crosswalk` | SOC 2010↔2018 occupation code mappings |

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
- **CPI-U deflation base year is 2023**: Real wage metrics use `CPI_BASE_YEAR = 2023` constant in `timeseries.py`. Formula: `real_wage = nominal × (CPI_2023 / CPI_year)`.
- **SOC crosswalk mapping types**: The crosswalk parser classifies each 2010→2018 code pair as 1:1, split, merge, or complex based on cardinality. Only 1:1 mappings are used for wage comparisons; splits/merges can aggregate employment counts.

## Pipeline Flow

Extract (declarative, manifest-driven) -> Parse (dataset-specific) -> Validate (structural, semantic, temporal, drift) -> Load (idempotent at dataset-version grain)

Logical pipelines: `taxonomy_refresh`, `oews_refresh`, `onet_refresh`, `projections_refresh`, `warehouse_publish`, `timeseries_refresh`. SOC must complete before occupation conformance; OEWS and O*NET may run independently. Time-series refresh runs after warehouse_publish.

## Testing Strategy

- **653+ tests** across four test directories:
  - `tests/unit/` — Fixture-based parser, loader, orchestration, validation, and config tests. No database or network needed.
  - `tests/web/` — FastAPI TestClient tests for all API endpoints, HTML pages, security headers, accessibility, and end-to-end smoke tests. No database needed (uses in-memory fixtures).
  - `tests/warehouse/` — Real data validation tests against `warehouse.duckdb`. **Automatically skipped** if the warehouse file is absent. Run `jobclass-pipeline run-all` first to populate it.
  - `tests/integration/` — End-to-end smoke tests and cross-layer integration tests.
- Parser unit tests on representative source files
- Schema contract tests (fail on missing/changed columns)
- Grain uniqueness tests (fail on duplicate business keys)
- Referential integrity tests (facts/bridges must point to existing dimensions)
- Historical regression tests against known published totals
- Idempotent rerun tests (no duplicate output on re-run)

## Completed Releases

**Release 1** — SOC hierarchy, OEWS national + state, O*NET core descriptors (skills, knowledge, abilities, tasks), warehouse schema with lineage/version tracking, repeatable orchestration, validation, five initial marts, web UI with occupation profiles, search, hierarchy browser, wage comparison, methodology page.

**Time-Series Release** — Multi-vintage OEWS (2021–2023), conformed metric catalog, time-period dimension, observation + derived-series facts, 5 time-series marts, trend explorer, occupation comparison, geography comparison, ranked movers, comparable history framework.

**Lessons Release** — 12 educational lesson pages covering federal data, dimensional modeling, multi-vintage challenges, data quality, time-series normalization, idempotent pipelines, static site generation, testing/deployment, similarity algorithms, thread safety, multi-vintage queries, and UI-data alignment.

**New Data Sources Release** — 7 new data sources (O*NET knowledge/abilities/work-activities/education/technology, BLS CPI-U, SOC crosswalk), CPI explorer pages, integrated code review fixes.

**Code Review V2 Release** — 18 findings across 4 phases: security hardening, performance optimization, code quality, and test coverage improvements.

**Pipeline Explorer Release** — Canvas-based interactive graph visualization of the entire JobClass pipeline at `/pipeline`. 57 nodes, 100+ edges, 10 lane groups. Semantic zoom (overview/subsystem/detail), smooth camera animation, guided educational modes (4 modes with intro overlay and pulse animation), node/edge interaction with detail panel, minimap with drag viewport, search/filter/overlay controls, domain filters, path isolation, cross-links to all 20 lessons and methodology, URL hash deep-linking, arrow-key navigation, reduced-motion support, 19 new tests.

Not in scope: HR job architecture, title normalization, international harmonization, real-time APIs.
