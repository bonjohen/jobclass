# Topics Learned

Lessons and issues discovered during the time-series labor intelligence implementation (Phases TS1–TS10) and deployment preparation.

## Data Issues

### BLS ZIP Files Contain Excel Temp Files
- **Problem:** The OEWS 2022 state ZIP (`oesm22st.zip`) contained an Excel temp/lock file `~$state_M2022_dl.xlsx` listed before the actual XLSX, causing "File is not a zip file" errors.
- **Fix:** Filter `~$` prefixed files in `extract_xlsx_from_zip` (`src/jobclass/extract/formats.py`).
- **Takeaway:** Always filter temp/lock files when extracting from ZIPs. BLS does not scrub these before publishing.

### BLS OEWS Broad/Detailed Group Overlap Creates Duplicates
- **Problem:** BLS OEWS data includes the same occupation in both "broad" and "detailed" groups with identical values. This created duplicate rows in `fact_occupation_employment_wages`, which then violated the unique constraint on `fact_time_series_observation` during normalization.
- **Fix:** Added `SELECT DISTINCT` to the time-series normalization query in `src/jobclass/load/timeseries.py`.
- **Takeaway:** BLS occupation groupings overlap by design. Any aggregation or normalization from OEWS facts must deduplicate.

### OEWS Column Names Vary Across Vintages
- **Problem:** Older OEWS XLSX files use different column headers (e.g., `GROUP` vs `OCC_GROUP` vs `O_GROUP`, `AREA_NAME` vs `AREA_TITLE`).
- **Fix:** Extended `_OEWS_COLUMN_ALIASES` in `src/jobclass/parse/oews.py` to normalize all known variations.
- **Takeaway:** When adding historical vintages, always check column headers against the parser's alias map.

### Occupation Similarity Was Broken by O\*NET's Universal Skill Ratings
- **Problem:** The `occupation_similarity_seeded` view used Jaccard similarity on binary skill presence/absence. But O\*NET rates all 35 skills for every occupation — they differ in importance scores, not presence. Jaccard produced 1.0 (100% similar) for every pair, making Dancer "similar" to Bakers, Lawyers, and Pile Driver Operators.
- **Secondary issue:** "All Other" catch-all occupations (e.g., `17-2199 Engineers, All Other`) had up to 8x duplicate rows per skill in `bridge_occupation_skill`, further corrupting the computation.
- **Fix:** Replaced Jaccard with cosine similarity on the importance (IM) score vectors. Added `AVG + GROUP BY` to deduplicate bridge rows before computing dot products. The view column is still named `jaccard_similarity` to avoid a cascading rename — the API exposes it as `similarity_score`.
- **Takeaway:** Before choosing a similarity algorithm, understand the data's structure. Binary presence/absence metrics are useless when every item has every feature rated. Use score-based similarity (cosine, correlation) when values carry the signal, not membership.

## Architecture Decisions

### Geography Dimension Must Be Shared Across Vintages
- **Problem:** Originally, `dim_geography` checked for existing rows using `geo_type + geo_code + source_release_id`, creating per-vintage geography keys. This broke cross-vintage YoY computations because the same physical area had different surrogate keys in each vintage.
- **Fix:** Changed the existence check to `geo_type + geo_code` only, so geography is shared across all vintages. Updated the fact table's geography lookup to match.
- **Takeaway:** Slowly changing dimensions that represent stable physical entities (like geographic areas) should deduplicate on business key only, not on source release.

### Multi-Vintage OEWS Extraction Uses Suffix-Based Pairing
- **Problem:** The original manifest had single `oews_national`/`oews_state` entries. Multi-vintage support required multiple entries per dataset type.
- **Fix:** Renamed to `oews_national_2021`, `oews_state_2021`, etc. The orchestrator (`run_all.py`) pairs national+state entries by matching their suffix after stripping the dataset prefix.
- **Takeaway:** Manifest naming convention matters for orchestration. Suffix-based pairing is simple and extensible.

### Static Site Cannot Fully Support Dynamic Comparison Queries
- **Problem:** The `/api/trends/compare/occupations` endpoint accepts arbitrary `soc_codes` query parameters. There are ~800 occupations, making it impossible to pre-generate all combinations.
- **Decision:** Pre-generate individual SOC trend JSON files and geography comparison files. The comparison page has limited functionality on the static site. The fetch shim handles geography comparison via `soc_code` parameter-to-filename mapping.
- **Takeaway:** Static site generation is inherently limited for endpoints with combinatorial query parameters. Accept graceful degradation rather than trying to pre-generate everything.

### DuckDB Connections Are Not Thread-Safe
- **Problem:** The web server shared a single DuckDB connection across all request threads. FastAPI runs sync endpoint handlers (`def`, not `async def`) in a thread pool. When two requests hit simultaneously (e.g., landing page fetching `/api/stats` and `/api/occupations/15-1252` in parallel), one thread's query could return empty results or corrupt data from the other.
- **Symptom:** Landing page stats intermittently showed 0 for Occupations, Tasks Tracked, etc. on refresh. The API returned correct data when tested sequentially via curl.
- **Fix:** Changed `database.py` to use `threading.local()` so each thread gets its own DuckDB connection. Added a `_test_conn` global fallback so test fixtures (which inject a connection from the main thread) still work across FastAPI's worker threads.
- **Takeaway:** DuckDB connections are not thread-safe. Any web framework that dispatches sync handlers to a thread pool (FastAPI, Flask with threaded mode) must use per-thread connections. Use `threading.local()` for production and a global override for test injection.

### Multi-Vintage Wages Endpoint Returned Duplicate Rows Per Geography
- **Problem:** The `/api/occupations/{soc_code}/wages?geo_type=state` endpoint returned all vintage rows for each state (e.g., 3 rows per state × 50 states = 150 rows instead of 50). The wages comparison page was designed to show the latest snapshot, not historical data.
- **Fix:** Added a filter on `source_release_id = MAX(source_release_id)` to the wages query in `src/jobclass/web/api/wages.py`, so only the latest OEWS release is returned.
- **Takeaway:** When multi-vintage data exists in fact tables, every endpoint must decide whether it shows latest-only or all-vintages. Wages comparison = latest only; trends = all vintages. Make the vintage filter explicit in every query.

### Derived Metrics Only Exist in Comparable Mode
- **Problem:** The Trend Explorer page defaulted to `as_published` comparability mode, but YoY absolute change and YoY percent change are only computed for `comparable` mode in `fact_derived_series`. All YoY columns showed N/A on the default view, making it look like the calculations were broken.
- **Fix:** Changed the default `<select>` option in `trend_explorer.html` from `as_published` to `comparable`, so users see YoY data immediately.
- **Takeaway:** When derived metrics depend on a specific comparability mode, the UI must default to that mode. Otherwise users see empty derived columns and assume the feature is broken. The API query was correct — the default just pointed at the wrong data slice.

### Movers Page Missing Absolute Change Context
- **Problem:** The Ranked Movers page only showed YoY percent change. Without the absolute dollar/count change, users couldn't distinguish meaningful moves from noise. A 200% increase on a $10,000 base is very different from 200% on a $100,000 base.
- **Fix:** Added a LEFT JOIN to `fact_derived_series` for `yoy_absolute_change` in the movers API query. Updated `ranked_movers.js` to display a "YoY Change" column with dollar formatting for wage metrics and count formatting for employment.
- **Takeaway:** Percentage changes without absolute context are misleading. Always show both when reporting movers/outliers.

### Static Site Fetch Shim Must Handle Dynamic Comparison Queries
- **Problem:** The `/trends/compare` page on the static site always showed "Failed to load comparison data." The fetch shim fell through to `F(b+p+'.json')` which tried to load a non-existent `occupations.json`. The compare/occupations API is inherently dynamic — it accepts arbitrary SOC code combinations.
- **Fix:** Added a shim handler that intercepts `/api/trends/compare/occupations`, fetches individual per-occupation trend JSON files (which are pre-generated), and assembles the comparison response client-side. Also added per-metric trend files (`-mean_annual_wage.json`, `-median_annual_wage.json`) so metric switching works. Added per-year movers files and shim routing for the year parameter.
- **Takeaway:** When a static site can't pre-generate an endpoint, check if the response can be assembled from existing pre-generated data. Client-side composition of pre-built JSON files can replicate server-side joins.

### Ranked Movers Mixed Years in a Single View
- **Problem:** The Ranked Movers page displayed all years' movers in one table with a "Year" column. This mixed 2022 and 2023 data together, making it impossible to compare within a single time period. Users needed to mentally filter by year.
- **Fix:** Added a `year` query parameter to the `/api/trends/movers` endpoint, defaulting to the latest year. The API returns `available_years` and the selected `year` in the response. The UI shows a year dropdown filter and removes the year column from the table since all rows now share the same year.
- **Takeaway:** When data has a time dimension, expose it as a filter control rather than a table column. Default to the most recent period so users see current data immediately.

### UI Elements Shown for Unavailable Data
- **Problem:** The occupation profile page displayed a "Compare by State" button for all 1,447 occupations. But 600 occupations (mostly broad groups and minor groups, plus 49 detailed occupations) have no state-level OEWS wage data. Clicking the button led to a dead-end page saying "No state-level wage data available."
- **Fix:** The "Compare by State" link is now hidden by default. After loading national wages, the JS fires a background check for state wages data and only reveals the link if data exists.
- **Takeaway:** Don't show navigation links to views that will be empty. Either pre-check data availability or hide-and-reveal after a fast background probe. A dead-end page erodes user trust more than a missing link.

## CI/CD Issues

### Ruff Format Must Run Before Push
- **Problem:** CI was failing because 63 files didn't match ruff's formatting rules. This blocked all pushes even though the code was functionally correct.
- **Fix:** Ran `ruff format src/ tests/` and committed the result.
- **Takeaway:** Run `ruff format --check src/ tests/` locally before pushing. Consider adding a pre-commit hook.

### Python Version Alignment
- **Problem:** CI was testing on Python 3.11/3.12 while local development used Python 3.14.
- **Fix:** Updated CI matrix to `[3.12, 3.14]` and lint to Python 3.14.
- **Takeaway:** Keep CI Python versions aligned with what developers actually use. Drop versions that are no longer relevant.

## Deployment Pipeline

### Static Site Must Be Rebuilt After Adding New Routes
- **Problem:** Adding trend pages (`/trends/*`) and trend API endpoints (`/api/trends/*`) to the web app does not automatically make them available on the GitHub Pages static site.
- **Fix:** Updated `scripts/build_static.py` to generate trend HTML pages (5 route types, per-SOC pages for explorer and geography) and trend API JSON files (metrics, movers, per-SOC trend data, geography comparison). Updated the fetch shim and path rewriting for trend URLs.
- **Takeaway:** Every new route or API endpoint in the web app requires a corresponding addition to `build_static.py`. The deployment process is: code change → test → commit → push → rebuild static site → deploy pages.

### Full Deployment Checklist
1. `ruff check src/ tests/` — lint passes
2. `ruff format --check src/ tests/` — formatting matches
3. `pytest tests/unit/ tests/web/ -q` — all tests pass
4. `git push` — CI passes on GitHub
5. `MSYS_NO_PATHCONV=1 python scripts/build_static.py --base-path /jobclass` — rebuild static site
6. `python scripts/deploy_pages.py` — deploy to GitHub Pages
