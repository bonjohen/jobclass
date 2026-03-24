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
