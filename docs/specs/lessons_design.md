# Lessons Section — Design & Content

This document defines the educational content for the "Lessons" section of the JobClass web application. Each lesson becomes a standalone page accessible from a landing page at `/lessons`. The nav bar gains a "Lessons" tab after "Methodology".

## Purpose

Someone returning to this project after months away should be able to read these lessons and understand:

- What federal labor data looks like and why it's harder than it appears
- The architectural decisions that shaped the warehouse and why alternatives were rejected
- The specific data quality traps that will bite you if you're not watching for them
- How time-series analysis works when your source data was never designed for it
- How the static site deployment works and where its limits are

Each lesson is self-contained. They build on each other loosely but can be read in any order.

---

## Lesson 1: The Federal Labor Data Landscape

**Slug:** `/lessons/federal-data`

### What You'll Learn

The four federal data products that feed this warehouse, what each one provides, and how they connect through the SOC code.

### Content

#### The Occupation Code Is Everything

Every data product in this system revolves around the Standard Occupational Classification (SOC) code. A SOC code like `11-1011` identifies "Chief Executives" — the `11` is the major group (Management), `1011` narrows to the specific occupation. There are roughly 870 detailed occupations in SOC 2018.

The SOC taxonomy is published by BLS and updated roughly every 10 years. The current version is SOC 2018. This matters because when the taxonomy changes, occupation codes can split, merge, or disappear — breaking any naive time-series comparison.

#### Four Data Products, One Key

| Source | Publisher | What It Contains | Update Frequency |
|--------|-----------|-----------------|------------------|
| **SOC** | BLS | Occupation hierarchy: major → minor → broad → detailed | ~10 years |
| **OEWS** | BLS | Employment counts and wage statistics by occupation, geography, and industry | Annual (May reference period) |
| **O\*NET** | DOL/O\*NET Center | Skills, knowledge, abilities, and tasks for each occupation | Continuous (versioned releases) |
| **Employment Projections** | BLS | 10-year employment outlook with growth rates | Every 2 years |

#### How They Connect

```
SOC (taxonomy backbone)
 ├── OEWS links via occupation_code → how many people, how much they earn
 ├── O*NET links via SOC code → what skills and tasks the job requires
 └── Projections link via SOC code → where employment is heading
```

The SOC taxonomy must load first. Every other data product joins to `dim_occupation` through the SOC code. If a source uses a code that doesn't exist in the loaded SOC version, that row is excluded (this is expected for ~5 NEM 2024 codes that don't map to SOC 2018).

#### Why This Matters

You cannot treat these as four independent datasets. They are four views of the same occupational reality, and the SOC code is the thread that connects them. Designing the warehouse around this fact — occupation as the stable external key — is the single most important architectural decision in this project.

---

## Lesson 2: Dimensional Modeling for Labor Data

**Slug:** `/lessons/dimensional-modeling`

### What You'll Learn

How the warehouse organizes data into dimensions, facts, and bridges — and why this structure makes querying straightforward while keeping the data honest.

### Content

#### The Four-Layer Architecture

```
Raw/Landing → Staging → Core Warehouse → Analyst Marts
```

Each layer has a specific job:

1. **Raw/Landing** — Store the downloaded file exactly as received. Never modify it. Record the URL, download time, checksum, and source release label. If something goes wrong downstream, you can always reprocess from raw.

2. **Staging** — Parse the raw file into relational tables. Standardize column names (everything becomes `snake_case`). Apply explicit typing. Do not interpret, aggregate, or transform business meaning. Example: `stage__bls__oews_national`.

3. **Core Warehouse** — Conform the staged data into shared dimensions and facts. This is where business meaning gets assigned. Dimensions (`dim_occupation`, `dim_geography`, `dim_industry`) provide the context; facts (`fact_occupation_employment_wages`) record the measurements; bridges (`bridge_occupation_skill`) link many-to-many relationships.

4. **Analyst Marts** — Pre-joined, denormalized views optimized for specific questions. No new business logic — only reshaping what the core warehouse already established. Example: `occupation_summary` joins occupation + wages + skills into one queryable view.

#### Why Dimensions Matter

A dimension table like `dim_geography` stores the descriptive attributes of a geographic area: its code (`37`), type (`state`), name (`North Carolina`), and whether it's the current version. The fact table stores only the surrogate key (`geography_key = 14`), not the full description.

This separation means:
- Geographic names can change without rewriting fact history
- Multiple facts can reference the same geography without storing redundant strings
- Queries filter on dimension attributes and join to facts via integer keys (fast)

#### The Grain Rule

Every fact table has a "grain" — the combination of dimensions that uniquely identifies a row. For `fact_occupation_employment_wages`, the grain is:

```
(reference_period, geography_key, industry_key, ownership_code, occupation_key, source_dataset)
```

If you insert a row that duplicates this grain, something has gone wrong. The loader enforces this with delete-before-insert at the `(source_dataset, source_release_id)` level.

#### Bridge Tables for Many-to-Many

An occupation has many skills. A skill applies to many occupations. The `bridge_occupation_skill` table resolves this with three columns: `occupation_key`, `element_id`, and a score. This is deliberately separate from a generic EAV table — each O\*NET domain (skills, knowledge, abilities, tasks) gets its own bridge table for clarity.

---

## Lesson 3: The Multi-Vintage Challenge

**Slug:** `/lessons/multi-vintage`

### What You'll Learn

What happens when you load multiple years of the same dataset, and the specific problems that arise when dimensions need to be shared across time.

### Content

#### What Is a "Vintage"?

A vintage is one release of a dataset. OEWS publishes annually with a May reference period, so `2021.05`, `2022.05`, and `2023.05` are three vintages of the same dataset. Each vintage is a complete snapshot — not a diff.

#### The Naive Approach (and Why It Breaks)

The simplest approach: load each vintage independently. Each vintage creates its own dimension rows. OEWS 2021 creates geography key 1 for "National", OEWS 2022 creates geography key 2 for "National", OEWS 2023 creates geography key 3 for "National".

Now try to compute year-over-year change in employment for a national-level occupation. You need to join facts from 2021 and 2023 on geography — but they have different geography keys for the same physical area. The join produces zero rows.

#### The Fix: Deduplicate on Business Key

Geography doesn't change between vintages. North Carolina is still North Carolina. So the geography dimension should check for existing rows using only the business key (`geo_type + geo_code`), not the source release. If a matching row exists, reuse its surrogate key.

**Before (broken):**
```sql
WHERE geo_type = ? AND geo_code = ? AND source_release_id = ?
```

**After (correct):**
```sql
WHERE geo_type = ? AND geo_code = ?
```

This single change — removing `source_release_id` from the geography lookup — is what makes cross-vintage time-series analysis possible.

#### Manifest-Based Vintage Management

The source manifest (`config/source_manifest.yaml`) uses suffix-based naming for vintages:

```yaml
- dataset_name: oews_national_2021
  dataset_url: https://www.bls.gov/oes/special-requests/oesm21nat.zip
- dataset_name: oews_national_2022
  dataset_url: https://www.bls.gov/oes/special-requests/oesm22nat.zip
- dataset_name: oews_national_2023
  dataset_url: https://www.bls.gov/oes/special-requests/oesm23nat.zip
```

The orchestrator pairs national + state entries by matching their suffix: `oews_national_2021` pairs with `oews_state_2021`. This convention is simple, extensible, and easy to debug.

---

## Lesson 4: Data Quality Traps in Government Sources

**Slug:** `/lessons/data-quality`

### What You'll Learn

The specific, non-obvious data quality issues in BLS and O\*NET source files that will cause pipeline failures if you don't handle them.

### Content

#### Trap 1: ZIP Files With Garbage Inside

BLS publishes OEWS data as ZIP files containing Excel spreadsheets. The 2022 state ZIP (`oesm22st.zip`) also contained `~$state_M2022_dl.xlsx` — an Excel temp/lock file that someone at BLS left in the archive. Our ZIP extractor tried to read this as the data file and failed with "File is not a zip file."

**Defense:** Filter any filename starting with `~$` before selecting the XLSX to extract. BLS does not scrub their archives before publishing.

```python
xlsx_names = [
    n for n in zf.namelist()
    if n.lower().endswith(".xlsx") and not n.split("/")[-1].startswith("~$")
]
```

#### Trap 2: Column Names Change Between Vintages

OEWS 2023 uses the column header `O_GROUP`. OEWS 2021 uses `OCC_GROUP`. Older files might use just `GROUP`. They all mean the same thing.

Similarly: `AREA_NAME` in one vintage, `AREA_TITLE` in another.

**Defense:** Maintain an alias map in the parser that normalizes all known column name variations to a single canonical name:

```python
_OEWS_COLUMN_ALIASES = {
    "group": "o_group",
    "occ_group": "o_group",
    "area_name": "area_title",
    ...
}
```

When adding a new vintage, the first thing to check is whether its column headers match the alias map.

#### Trap 3: Broad/Detailed Group Overlap

BLS categorizes occupations into hierarchical groups: major, minor, broad, and detailed. In the OEWS data, a "detailed" occupation like `11-1011` (Chief Executives) also appears under its "broad" group `11-1010`. Both rows carry identical employment counts and wage values.

If you load both rows into the fact table and then try to normalize into time-series observations, the unique constraint fires because you're inserting the same `(occupation_key, geography_key, period_key)` twice with the same values.

**Defense:** Use `SELECT DISTINCT` when normalizing from fact to time-series observation tables. The duplicates have identical values, so deduplication is safe and correct.

#### Trap 4: Suppressed Values Are Not Zeros

BLS suppresses wage and employment data for confidentiality when the number of respondents is too small. These values arrive as null, asterisks (`*`), or special markers (`**`). They mean "data exists but cannot be disclosed" — fundamentally different from zero.

**Defense:** Preserve nulls through every layer. Never impute, never substitute zero. Display "Data suppressed" or "Not available" in the UI. This is a legal and ethical requirement, not just a data quality preference.

#### Trap 5: BLS Blocks Bare HTTP Requests

BLS.gov returns 403 Forbidden for HTTP requests that don't include browser-like headers. Specifically, you need `Sec-Fetch-Dest`, `Sec-Fetch-Mode`, `Sec-Fetch-Site`, and `Sec-Fetch-User` headers.

**Defense:** The downloader sends a full set of browser-like headers. This is not scraping — the data is public — but BLS's CDN enforces these checks.

---

## Lesson 5: Time-Series Normalization

**Slug:** `/lessons/time-series`

### What You'll Learn

How to transform point-in-time fact table snapshots into proper time-series data, and why "as published" and "comparable history" are two different products.

### Content

#### The Problem: Facts Are Snapshots, Not Series

The `fact_occupation_employment_wages` table stores one row per (occupation, geography, period, release). It records "in OEWS release 2023.05, occupation 11-1011 in the national scope had employment of 200,480." This is a snapshot — a single measurement at a single point in time.

To answer "how has employment for Chief Executives changed from 2021 to 2023?", you need to pull three snapshots and align them by time period. That's what time-series normalization does.

#### The Time-Series Schema

```
dim_time_period          — (period_key, year, period_type)
dim_metric               — (metric_key, metric_name, display_name, unit)
fact_time_series_observation — (occupation_key, geography_key, period_key, metric_key, value, ...)
fact_derived_series      — (occupation_key, geography_key, period_key, metric_key, value, ...)
```

Base observations come from the fact table. Derived series (YoY change, rolling averages, state-vs-national gap) are computed from base observations. The two are stored separately because derived values should never be treated as source data.

#### Two Modes: As Published vs. Comparable

**As Published** preserves every observation exactly as it appeared in its source release. If BLS published employment = 200,480 in OEWS 2023.05, that value goes into the time series regardless of whether the SOC taxonomy changed between releases.

**Comparable History** only includes observations from vintages that share the same SOC taxonomy version. If OEWS 2021, 2022, and 2023 all use SOC 2018, all three are comparable. But if a future release uses SOC 2028 with different occupation definitions, comparing its employment count to a SOC 2018 count would be misleading.

Both modes are always computed. The UI lets the user choose which view they want.

#### Derived Metrics

From base observations, the pipeline computes:

| Metric | Formula | Minimum Data Required |
|--------|---------|----------------------|
| Year-over-year absolute change | `value(year) - value(year-1)` | 2 consecutive years |
| Year-over-year percent change | `(value(year) - value(year-1)) / value(year-1) * 100` | 2 consecutive years |
| 3-year rolling average | `avg(value) over 3-year window` | 3 consecutive years |
| State vs. national gap | `state_value - national_value` for same occupation/period | State + national data |
| Rank delta | `rank(year-1) - rank(year)` (positive = improved) | 2 consecutive years |

These derived values are labeled as such in the database and the UI. They are never mixed with source observations.

---

## Lesson 6: Idempotent Pipeline Design

**Slug:** `/lessons/idempotent-pipelines`

### What You'll Learn

Why every load operation must be safely re-runnable, and the specific patterns that make this work.

### Content

#### Why Idempotency Matters

Data pipelines fail. Downloads timeout, parsers hit unexpected formats, database connections drop. When you restart the pipeline, it must not create duplicate rows for data that was already loaded.

Idempotency means: running the same operation twice produces the same result as running it once.

#### Pattern: Delete-Before-Insert at Release Grain

The OEWS loader uses this pattern:

```sql
-- 1. Delete any existing rows for this release
DELETE FROM stage__bls__oews_national WHERE source_release_id = ?

-- 2. Insert the new rows
INSERT INTO stage__bls__oews_national (...) VALUES (...)
```

If the pipeline crashes after step 1 but before step 2, the next run will delete nothing (already gone) and insert fresh. If it crashes after both steps, the next run will delete the partial data and re-insert complete. Either way, no duplicates.

#### Pattern: Check-Before-Insert for Dimensions

Dimension tables use existence checks:

```sql
-- Only insert if this business key doesn't already exist
INSERT INTO dim_geography (geo_type, geo_code, geo_name, ...)
SELECT ?, ?, ?, ...
WHERE NOT EXISTS (
    SELECT 1 FROM dim_geography WHERE geo_type = ? AND geo_code = ?
)
```

This means the dimension grows over time (new geographies get added) but existing rows are never duplicated or modified.

#### Pattern: Fact Table Grain Uniqueness

The fact table's unique constraint on its grain columns is the final safety net. Even if the loader logic has a bug, the database will reject duplicate facts:

```sql
UNIQUE (reference_period, geography_key, industry_key, ownership_code,
        occupation_key, source_dataset)
```

Every test suite includes idempotence tests: load data, record the row count, load again, verify the count hasn't changed.

---

## Lesson 7: Static Site Generation

**Slug:** `/lessons/static-site`

### What You'll Learn

How a dynamic FastAPI application gets converted into a static GitHub Pages site, and where the approach has inherent limitations.

### Content

#### The Problem

The web application runs FastAPI with server-side template rendering and JSON API endpoints. GitHub Pages serves only static files — no Python, no server-side logic. We need to pre-generate every page and every API response as files.

#### The Approach

`scripts/build_static.py` uses FastAPI's `TestClient` to request every page and API endpoint from the running application, then writes the responses to files:

```
HTML pages  → _site/occupation/11-1011/index.html
API JSON    → _site/api/occupations/11-1011.json
```

A JavaScript "fetch shim" is injected into every HTML page's `<head>`. It intercepts `fetch()` calls to `/api/` URLs and redirects them to the corresponding `.json` files. The page's JavaScript doesn't know it's running on a static site — it fetches data the same way it would from a live server.

#### How the Fetch Shim Works

```
Page JS calls:  fetch('/api/occupations/11-1011/wages?geo_type=state')
Shim maps to:   fetch('/api/occupations/11-1011/wages-state.json')
```

For search, the shim downloads the full occupation index once, caches it, and filters client-side — no server needed.

For geography comparison trends, the shim maps the `soc_code` query parameter to a filename:
```
fetch('/api/trends/compare/geography?soc_code=11-1011')
→ fetch('/api/trends/compare/geography-11-1011.json')
```

#### The Limitation: Combinatorial Endpoints

The `/api/trends/compare/occupations?soc_codes=11-1011,13-1011,15-1211` endpoint accepts arbitrary combinations of SOC codes. With ~870 occupations, the number of possible combinations is astronomical. You cannot pre-generate all of them.

This is a fundamental limitation of static site generation: endpoints with combinatorial query parameters cannot be fully pre-rendered. The static site accepts graceful degradation here — comparison features have reduced functionality compared to the live server.

#### Path Rewriting for GitHub Pages

GitHub Pages serves this site at `/jobclass/` (a subpath), not at the root. Every absolute URL in the HTML (`/api/`, `/static/`, `/occupation/`, `/trends/`) must be rewritten to include the base path (`/jobclass/api/`, etc.). The `rewrite_paths()` function handles this with string replacements before the shim is injected.

The shim itself does NOT need path rewriting — it extracts the base path from the URL at runtime using `u.indexOf('/api/')`.

#### Adding New Routes to the Static Site

Every new route or API endpoint in the web app must also be added to `build_static.py`. The checklist:

1. Add HTML page generation (the `write_html()` calls)
2. Add API JSON generation (the `write_json()` calls)
3. Add path rewriting entries for new URL prefixes
4. Update the fetch shim if the endpoint uses query parameters that need filename mapping
5. Rebuild and deploy

---

## Lesson 8: Testing and Deployment

**Slug:** `/lessons/testing-deployment`

### What You'll Learn

The testing strategy, how CI works, and the full deployment pipeline from code change to live site.

### Content

#### Three Test Directories

| Directory | What It Tests | Requirements |
|-----------|--------------|-------------|
| `tests/unit/` | Parsers, loaders, orchestration, validation, config | Fixtures only — no database, no network |
| `tests/web/` | API endpoints, HTML pages, security headers, accessibility | In-memory fixtures via TestClient |
| `tests/warehouse/` | Real data validation against `warehouse.duckdb` | Populated warehouse (auto-skipped if absent) |

Unit and web tests run in CI on every push and PR. Warehouse tests run only locally after `jobclass-pipeline run-all`.

#### What the Tests Actually Verify

- **Schema contracts:** Required columns exist on every table
- **Grain uniqueness:** No duplicate business keys in any dimension or fact
- **Referential integrity:** Every fact row's dimension keys point to existing dimension rows
- **Idempotence:** Re-running a load produces the same row count
- **Validation framework:** Structural, temporal, and drift checks all pass
- **API correctness:** Every endpoint returns expected status codes and response shapes
- **Security:** CSP headers, no PII exposure, CORS configuration

#### CI Configuration

GitHub Actions runs on every push to `main` and every PR:

```yaml
lint:
  python-version: "3.14"
  steps: ruff check + ruff format --check

test:
  matrix: [3.12, 3.14]
  steps: pip install -e ".[dev]" → pytest --cov
```

**Key lesson:** Run `ruff format --check src/ tests/` locally before pushing. CI will reject unformatted code even if it's functionally correct.

#### Full Deployment Pipeline

```
1. ruff check src/ tests/              # Lint passes
2. ruff format --check src/ tests/     # Formatting matches
3. pytest tests/unit/ tests/web/ -q    # All tests pass
4. git push                            # CI passes on GitHub
5. python scripts/build_static.py \
     --base-path /jobclass             # Rebuild static site
6. python scripts/deploy_pages.py      # Deploy to GitHub Pages
```

Steps 1-4 ensure code quality. Step 5 regenerates every HTML page and JSON file (takes several minutes for ~870 occupations). Step 6 force-pushes `_site/` to the `gh-pages` branch.

---

## Web Implementation Plan

### Navigation

Add "Lessons" to `base.html` nav after "Methodology":
```html
<li><a href="/lessons">Lessons</a></li>
```

### Routes

| URL | Template | Description |
|-----|----------|-------------|
| `/lessons` | `lessons.html` | Landing page with lesson index |
| `/lessons/federal-data` | `lessons_federal_data.html` | Lesson 1 |
| `/lessons/dimensional-modeling` | `lessons_dimensional_modeling.html` | Lesson 2 |
| `/lessons/multi-vintage` | `lessons_multi_vintage.html` | Lesson 3 |
| `/lessons/data-quality` | `lessons_data_quality.html` | Lesson 4 |
| `/lessons/time-series` | `lessons_time_series.html` | Lesson 5 |
| `/lessons/idempotent-pipelines` | `lessons_idempotent_pipelines.html` | Lesson 6 |
| `/lessons/static-site` | `lessons_static_site.html` | Lesson 7 |
| `/lessons/testing-deployment` | `lessons_testing_deployment.html` | Lesson 8 |

### Static Site Integration

- Add all lesson pages to `build_static.py` `write_html()` calls
- Add `/lessons` path rewriting for GitHub Pages base path
- No API endpoints needed — all content is static HTML

### CSS

Reuse `.methodology-page` / `.methodology-section` patterns with a `.lessons-page` class. Code blocks should use a `<pre><code>` pattern with a monospace background.

### Landing Page Design

The `/lessons` landing page should display:
- A brief intro explaining the purpose
- A card grid with each lesson's title, a one-line description, and estimated reading time
- Cards link to the individual lesson pages
- Lessons ordered by topic flow (data sources → modeling → challenges → deployment)
