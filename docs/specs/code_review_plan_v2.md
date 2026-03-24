# Code Review V2 — Findings and Remediation Plan

## 1. Executive Summary

The JobClass codebase has matured substantially since the V1 review. All 26 original findings have been addressed — 24 fully fixed, 2 partially fixed. The project now has CI/CD, security headers, input validation, CLI entrypoints, a Dockerfile, Pydantic response models, centralized escapeHtml, extracted JS files, thread-safe connections, a metrics endpoint, and 585+ tests.

The most important concerns in the current codebase, in priority order:

1. **No tests for the static site build pipeline.** `build_static.py` generates the entire GitHub Pages deployment — URL rewriting, fetch shim injection, search index generation, per-year/per-metric JSON file creation — with zero test coverage. A regression in the shim silently breaks the public site.

2. **`fetchWithTimeout` duplicated in 10 JavaScript files.** The same 5-line function is copy-pasted across nearly every JS file instead of being defined once in `main.js`. This is the exact same class of duplication that V1 flagged for `escapeHtml`, now repeated for a different utility.

3. **Lesson slug lists maintained in 3 separate files.** Adding a lesson requires updating `app.py`, `test_lessons.py`, and `build_static.py` independently. No mechanism ensures they stay in sync.

4. **Trends API lacks Pydantic response models.** Every other API router uses typed response models from `models.py`. The trends router returns untyped `dict`, breaking the contract consistency pattern.

5. **Test coverage is shallow for new features.** The ranked movers year filter, geography comparison parameters, occupation comparison edge cases, and static site shim routing all lack targeted tests.

---

## 2. V1 Remediation Status

| # | V1 Finding | Status | Evidence |
|---|-----------|--------|----------|
| 1 | XSS via innerHTML | **Fixed** | `escapeHtml()` centralized in `main.js`; all templates use `textContent` or escaped DOM construction |
| 2 | SQL injection via f-string table names | **Fixed** | `health.py` uses `_safe_identifier()` with regex validation; `framework.py` validates identifiers |
| 3 | No CORS middleware | **Fixed** | `CORSMiddleware` in `app.py:39-44` |
| 4 | No CSP header | **Fixed** | `CSPMiddleware` in `app.py:46-56` with `X-Content-Type-Options` and `X-Frame-Options` |
| 5 | No CLI entrypoints | **Fixed** | `jobclass-pipeline` and `jobclass-web` in `pyproject.toml [project.scripts]` |
| 6 | Config path duplication | **Fixed** | `database.py` imports `DB_PATH` and `MIGRATIONS_DIR` from `settings.py` |
| 7 | Parser utility duplication | **Fixed** | `parse/common.py` has shared `SUPPRESSION_MARKERS`, `parse_float()`, `parse_int()` |
| 8 | No input validation on API | **Fixed** | All endpoints validate SOC format, geo_type enum, search length. 400 responses for invalid input |
| 9 | Thread-unsafe connection init | **Fixed** | `threading.Lock()` + thread-local storage in `database.py` |
| 10 | Broad exception swallowing | **Partially Fixed** | Most locations improved; `trends.py:28` still catches bare `Exception` in `_table_exists()` |
| 11 | Search race condition | **Fixed** | `search.js` uses `AbortController` |
| 12 | Vague test assertions | **Fixed** | Tests use exact expected values throughout |
| 13 | No negative tests | **Fixed** | `test_cr1_security.py` has invalid input tests; 400 response validation throughout |
| 14 | Deep fixture chains | **Fixed** | Independent per-source fixtures available |
| 15 | No CI/CD | **Fixed** | `.github/workflows/ci.yml` with Python 3.12/3.14 matrix, ruff + pytest |
| 16 | No Dockerfile | **Fixed** | Multi-stage Dockerfile with health check |
| 17 | No dependency lock file | **Fixed** | `requirements.lock` and `requirements-dev.lock` present |
| 18 | No API pagination | **Fixed** | Search and wages endpoints have `limit`/`offset` parameters |
| 19 | Missing aria-live regions | **Fixed** | `aria-live="polite"` on all dynamic content sections |
| 20 | No fetch timeouts | **Fixed** | `fetchWithTimeout` in all page JS files (10s timeout) |
| 21 | No static cache-busting | **Fixed** | `base.html` uses `?v=CR4` query parameter on CSS/JS |
| 22 | Weak health endpoint | **Fixed** | `SELECT 1` connectivity check, migration validation, 503 on failure |
| 23 | No operational documentation | **Fixed** | CLAUDE.md and README have build/run/deploy commands |
| 24 | No metrics export | **Fixed** | `/api/metrics` returns Prometheus-formatted metrics |
| 25 | Hardcoded magic numbers | **Partially Fixed** | Some thresholds moved to constants; drift thresholds still inline in `framework.py` |
| 26 | Missing API versioning | **Not Addressed** | Endpoints still at `/api/` without version prefix — acceptable for current scope |

**Summary: 24 Fixed, 2 Partially Fixed, 0 Not Addressed (V1-26 is a design-for-future item, not a deficiency).**

---

## 3. Phased Release Plan

### Phase 1: Foundation and Clarity

**Goal:** Fix issues that affect correctness, consistency, or could cause silent failures on the public site.

---

#### CR2-01 — Extract `fetchWithTimeout` to `main.js`

**Area:** Implementation
**Severity:** High
**Evidence:** The identical 5-line function is copy-pasted in 10 JavaScript files:
- `geography_comparison.js:10-14`
- `hierarchy.js:8-12`
- `landing.js:7-11`
- `methodology.js` (similar lines)
- `occupation.js:10-14`
- `occupation_comparison.js:14-18`
- `ranked_movers.js:11-15`
- `trend_explorer.js:11-15`
- `trends.js:7-11`
- `wages.js` (similar lines)

**Why it matters:** This is the same duplication pattern that V1 found with `escapeHtml`. If the timeout value or abort behavior needs to change, 10 files must be edited. A missed file creates inconsistent behavior. `search.js` already diverges — it uses an inline pattern with different variable names and controller reuse semantics.

**Recommended change:**
- Define `fetchWithTimeout(url, timeoutMs)` in `main.js` alongside `escapeHtml` and `escapeAttr`.
- Remove the local definition from all 10 files.
- Update `search.js` to use the shared function (with a fresh controller per call to avoid reuse issues).
- Keep the `FETCH_TIMEOUT_MS = 10000` constant in `main.js`.

**Recommended validation:**
- All existing web tests pass.
- Manual test: verify fetch timeout still triggers error UI on all pages.
- Grep for `fetchWithTimeout` confirms only one definition exists (in `main.js`).

---

#### CR2-02 — Centralize Lesson Slug Registry

**Area:** Design
**Severity:** High
**Evidence:** The lesson slug list is maintained independently in three files:
- `src/jobclass/web/app.py:159-190` — `valid_slugs` dict (slug → title, template)
- `tests/web/test_lessons.py:3-16` — `LESSON_SLUGS` list
- `scripts/build_static.py:259-272` — `lesson_slugs` list

Adding a lesson requires updating all three, plus creating the template file. No mechanism detects drift between them.

**Why it matters:** Lesson 12 was recently added. The next lesson addition has a high probability of missing one of the three locations, causing either a broken static site (build_static misses it) or false-passing tests (test file doesn't include it).

**Recommended change:**
- Create a canonical registry in the web layer: `src/jobclass/web/lessons.py` with a `LESSONS` list of `(slug, title, template_name)` tuples.
- Import from this registry in `app.py`, `test_lessons.py`, and `build_static.py`.
- Single source of truth: add a lesson by adding one entry to `lessons.py` and creating the template.

**Recommended validation:**
- All existing lesson tests pass.
- Add a test that verifies every entry in the registry has a corresponding template file.
- Verify `build_static.py` generates all lesson pages from the registry.

---

#### CR2-03 — Add Pydantic Response Models to Trends API

**Area:** Implementation
**Severity:** Medium
**Evidence:** `src/jobclass/web/api/trends.py` — all 7 endpoints return `-> dict` without response models. Every other API router (`occupations.py`, `wages.py`, `skills.py`, `projections.py`, `health.py`, `methodology.py`) uses typed Pydantic models from `models.py`.

**Why it matters:** The trends API is the largest router (264 lines, 7 endpoints). Without response models:
- API documentation (`/docs`) shows untyped responses for trend endpoints.
- Contract tests cannot validate response shapes.
- Frontend code relies on implicit assumptions about field names.

**Recommended change:**
- Add models to `src/jobclass/web/api/models.py`: `TrendSeriesResponse`, `TrendCompareResponse`, `TrendGeographyResponse`, `TrendMoversResponse`, `AvailableYearsResponse`.
- Apply `response_model=` to each trends endpoint.

**Recommended validation:**
- Existing trend tests continue passing.
- Add a contract test that validates each trend response against its Pydantic model.
- Verify `/docs` shows typed schemas for all trend endpoints.

---

#### CR2-04 — Fix `_table_exists()` Exception Handling

**Area:** Implementation
**Severity:** Medium
**Evidence:** `src/jobclass/web/api/trends.py:26-28`:
```python
def _table_exists(table_name: str) -> bool:
    try:
        get_db().execute(f"SELECT 1 FROM {table_name} LIMIT 0")
        return True
    except Exception:
        return False
```

**Why it matters:** Catching bare `Exception` masks real errors (type errors, connection failures, permission issues). If the database file is corrupted or the connection pool is exhausted, `_table_exists` returns `False` instead of propagating the error, and the trends pages silently show "no data available" instead of an error message.

**Recommended change:**
- Import DuckDB-specific exceptions: `from duckdb import CatalogException, IOException`.
- Catch `CatalogException` for missing tables, `IOException` for connection issues (re-raise).
- Validate `table_name` against an allowlist before using in f-string SQL (matches the pattern in `health.py`'s `_safe_identifier()`).

**Recommended validation:**
- Test that `_table_exists("nonexistent_table")` returns `False`.
- Test that a corrupted connection propagates the error (not silently returns `False`).

---

### Phase 2: Correctness and Maintainability

**Goal:** Improve code quality, reduce duplication, and address patterns that make the system harder to extend.

---

#### CR2-05 — Static Site Shim Error Handling

**Area:** Implementation
**Severity:** Medium
**Evidence:** `scripts/build_static.py` lines 84-86 (within the STATIC_SHIM JavaScript):
```javascript
.catch(function(){return null})
```

In the occupation comparison shim handler, when fetching per-occupation trend JSON fails (404, network error), the catch returns `null`. This null propagates into the assembled response as an occupation with no series data. The frontend JavaScript (`occupation_comparison.js`) does not check for null occupations — it assumes all fetched occupations have valid `series` arrays.

**Why it matters:** If a single occupation's trend data file is missing from the static site, the comparison page shows a JavaScript error rather than a graceful "data unavailable" message.

**Recommended change:**
- Filter null results from the assembled occupations array before returning the response.
- Add a console warning in the shim when an occupation fetch fails.
- In `occupation_comparison.js`, add a null check before iterating series data.

**Recommended validation:**
- Delete one occupation's trend JSON from `_site/`, load the comparison page, verify graceful degradation.

---

#### CR2-06 — `search.js` AbortController Reuse

**Area:** Implementation
**Severity:** Medium
**Evidence:** `src/jobclass/web/static/js/search.js:22-25` — the `abortController` variable is reused across debounced searches. When a new search fires, the previous controller is aborted (`abortController.abort()` on line 24), then a new one is created. However, the timeout `clearTimeout` for the previous request's timer is not called, leaving orphaned timers.

**Why it matters:** Under rapid typing, orphaned timeout callbacks fire and call `.abort()` on already-completed or already-aborted controllers. While this doesn't cause visible bugs today (aborting a completed fetch is a no-op), it's a leak pattern that could cause unexpected behavior if the code is extended.

**Recommended change:**
- After extracting `fetchWithTimeout` to `main.js` (CR2-01), refactor `search.js` to use the shared function. Each call gets a fresh controller and cleans up its own timer.

**Recommended validation:**
- Existing search tests pass.
- Manual test: type rapidly, verify no console errors or stale results.

---

#### CR2-07 — Hardcoded Timeout Constant in 10 JS Files

**Area:** Implementation
**Severity:** Low
**Evidence:** `FETCH_TIMEOUT_MS = 10000` is defined independently in each JS file that uses `fetchWithTimeout`. If the timeout needs to change (e.g., for a slow server or mobile users), 10 files must be edited.

**Why it matters:** Resolved by CR2-01 (extracting to `main.js`). Listed separately to ensure the constant is also centralized, not just the function.

**Recommended change:** Part of CR2-01 — define `FETCH_TIMEOUT_MS` once in `main.js`.

---

#### CR2-08 — CSS Growing Monolithically

**Area:** Design
**Severity:** Low
**Evidence:** `src/jobclass/web/static/css/main.css` is 1,076 lines in a single file. Sections are not delimited by comments. Related styles (trends charts, lesson pages, occupation profiles) are intermixed.

**Why it matters:** At the current size, the CSS is manageable. But the project has grown from ~6 pages to ~20 pages, and the CSS has grown proportionally. Without section markers or modularization, finding the right styles for a specific page requires searching rather than navigating.

**Recommended change:**
- Add section comment headers (e.g., `/* === Trends Charts === */`, `/* === Lesson Pages === */`).
- No need to split into separate files at this scale — section comments are sufficient.
- Audit for repeated values that should be CSS variables (border-radius `6px`, `4px`, `8px` used inconsistently).

**Recommended validation:**
- Visual regression: all pages render identically after adding comments.
- Grep for repeated magic numbers; replace with variables where used 3+ times.

---

#### CR2-09 — Drift Threshold Magic Numbers

**Area:** Implementation
**Severity:** Low
**Evidence:** `src/jobclass/validate/framework.py` — drift detection thresholds (`20.0%`, `15.0%`) are inline numeric literals. No documentation explains why these specific values were chosen.

This was V1-25, partially addressed. The values remain inline.

**Recommended change:**
- Move to named constants at the top of the file with a comment explaining the rationale (e.g., `# 20% threshold chosen based on historical OEWS refresh variance`).

**Recommended validation:** Existing validation tests pass unchanged.

---

### Phase 3: Test and Release Confidence

**Goal:** Close test coverage gaps, add CI verification for the static site, and strengthen confidence in new features.

---

#### CR2-10 — Add Static Site Build Tests

**Area:** Testing
**Severity:** Critical
**Evidence:** `scripts/build_static.py` (380+ lines) has zero test coverage. This script:
- Renders all HTML pages via TestClient
- Injects the fetch shim JavaScript into every page
- Rewrites all URLs for the `/jobclass` base path
- Generates per-occupation, per-metric, per-year JSON files
- Builds a client-side search index
- Creates `.nojekyll` and copies static assets

A bug in any of these steps breaks the public GitHub Pages site silently.

**Why it matters:** The static site is the primary public-facing deployment. It is more complex than the live server (client-side composition, shim routing) and the only deployment path with zero automated verification.

**Recommended change:**
- Create `tests/test_build_static.py` with:
  - Test that HTML pages contain the shim script tag.
  - Test that URLs are rewritten to include the base path.
  - Test that per-year movers JSON files are generated for each available year.
  - Test that per-metric trend JSON files exist for wage metrics.
  - Test that the search index JSON is valid and contains occupation entries.
  - Test that all lesson pages are generated.
  - Test that `.nojekyll` exists in output.

**Recommended validation:**
- CI runs the static site build test.
- Intentionally break the shim (e.g., wrong URL pattern); verify the test fails.

---

#### CR2-11 — Add Tests for Ranked Movers Year Filter

**Area:** Testing
**Severity:** High
**Evidence:** `tests/web/test_trends.py` — `test_movers()` tests the default movers endpoint but does not test:
- Explicit year parameter (`?year=2023`).
- `available_years` field in response.
- Year that doesn't exist in data.
- Interaction between year and metric parameters.

**Why it matters:** The year filter was a recent addition. The ranked movers page on the static site generates per-year JSON files. If the API year parameter breaks, the static site serves stale default-year data with no indication of failure.

**Recommended change:**
- Add tests to `test_trends.py`:
  - `test_movers_with_year` — verify `year` parameter filters results.
  - `test_movers_available_years` — verify response includes `available_years` list.
  - `test_movers_invalid_year` — verify graceful handling of year not in data.
  - `test_movers_year_metric_combination` — verify year filter works with each metric.

**Recommended validation:** All new tests pass with test fixtures; fail when year filtering logic is removed.

---

#### CR2-12 — Add Tests for Trends Comparison Endpoints

**Area:** Testing
**Severity:** Medium
**Evidence:** `tests/web/test_trends.py` has basic 200-status tests for comparison endpoints but does not test:
- Occupation comparison with >10 codes (should reject).
- Occupation comparison with invalid SOC code format.
- Geography comparison with year parameter.
- Geography comparison with different metrics.
- Comparison with occupation that has no trend data.

**Why it matters:** The comparison endpoints are the most complex in the trends API — they join multiple tables, accept multiple parameters, and their static site shim does client-side composition. Untested edge cases are likely to fail silently.

**Recommended change:**
- Add tests for parameter validation (>10 codes rejected, invalid format returns 400).
- Add tests for empty data scenarios (occupation with no time series).
- Add tests for metric parameter propagation.

**Recommended validation:** New tests fail when corresponding validation is removed.

---

#### CR2-13 — Add CI Step for Static Site Build

**Area:** Deployment
**Severity:** Medium
**Evidence:** `.github/workflows/ci.yml` runs `ruff` and `pytest` but does not build the static site. A change to templates, API responses, or the build script can break the static site without CI catching it.

**Why it matters:** The static site is deployed manually (`scripts/deploy_pages.py`). Without CI verification, a developer could merge changes that pass tests but produce a broken static site.

**Recommended change:**
- Add a CI job or step that runs `python scripts/build_static.py --base-path /jobclass`.
- Verify the build completes without errors.
- Optionally, run a basic smoke test on the output (check that `_site/index.html` exists and contains expected content).

**Recommended validation:** Intentionally break a template; verify CI fails on the static site build step.

---

#### CR2-14 — Add Contract Tests for Trends Response Shapes

**Area:** Testing
**Severity:** Low
**Evidence:** After CR2-03 adds Pydantic models for trends, contract tests should verify that actual API responses conform to those models.

**Recommended change:**
- For each trends endpoint, parse the response JSON through the Pydantic model and assert no validation errors.
- This catches field renames, type changes, and missing fields automatically.

**Recommended validation:** Intentionally rename a field in the SQL query; verify the contract test fails.

---

### Phase 4: Operational and Reviewer Polish

**Goal:** Improve developer experience, documentation accuracy, and long-term maintainability.

---

#### CR2-15 — Add Version Rotation for Cache-Busting

**Area:** Deployment
**Severity:** Low
**Evidence:** `base.html` uses `?v=CR4` for cache busting. This version string must be manually updated when CSS or JS changes. There is no automation or documentation for when to update it.

**Why it matters:** If a developer changes CSS but forgets to bump the version, users see stale styles until their browser cache expires.

**Recommended change:**
- Document the cache-busting convention in CLAUDE.md (update `?v=` when CSS/JS changes).
- Alternatively, generate the version from a content hash during the build process.

**Recommended validation:** Change a CSS rule, update the version, verify the change is visible without clearing cache.

---

#### CR2-16 — Document Static Site Architecture

**Area:** Methodology
**Severity:** Low
**Evidence:** CLAUDE.md has a "Static Site / GitHub Pages" section, but it doesn't document:
- The full list of shim-handled URL patterns.
- How per-year and per-metric JSON files are named.
- The client-side composition pattern for comparison endpoints.
- How to test the static site locally before deploying.

**Why it matters:** A developer unfamiliar with the shim cannot safely modify it without understanding all the URL routing patterns.

**Recommended change:**
- Expand the Static Site section in CLAUDE.md with:
  - URL pattern → JSON file mapping table.
  - Client-side composition explanation for comparison endpoints.
  - Local testing instructions (`python -m http.server -d _site` or similar).

**Recommended validation:** A new developer can read the docs and understand the shim without reading the source.

---

#### CR2-17 — Add `deploy_pages.py` Sanity Checks

**Area:** Deployment
**Severity:** Low
**Evidence:** `scripts/deploy_pages.py` force-pushes to `gh-pages` without:
- Verifying `_site/` has expected structure (index.html, static/, api/).
- Checking for uncommitted changes in the main repo.
- Providing a dry-run mode.

**Why it matters:** An incomplete or corrupted `_site/` directory could be pushed to production, breaking the public site.

**Recommended change:**
- Add assertions that `_site/index.html`, `_site/static/`, and `_site/api/` exist before pushing.
- Add a `--dry-run` flag that shows what would be pushed without pushing.
- Remove the redundant `except Exception: pass` (line 59) since `ignore_errors=True` handles the same case.

**Recommended validation:** Delete `_site/index.html`; verify the script refuses to deploy.

---

#### CR2-18 — Remove Redundant Exception Handler in deploy_pages.py

**Area:** Implementation
**Severity:** Low
**Evidence:** `scripts/deploy_pages.py:57-61`:
```python
try:
    shutil.rmtree(site_dir / ".git", ignore_errors=True)
except Exception:
    pass
```

The `ignore_errors=True` already suppresses all errors from `shutil.rmtree`. The outer `try/except` is dead code.

**Recommended change:** Remove the `try/except` wrapper; keep only `shutil.rmtree(site_dir / ".git", ignore_errors=True)`.

**Recommended validation:** Deploy script still works after change.

---

## 4. Highest-Risk Areas

1. **Static site build pipeline** — Zero test coverage for the most complex deployment artifact. A shim bug silently breaks the public site. This is the highest-risk area in the current codebase.

2. **Static site fetch shim** — 72 lines of minified JavaScript embedded as a Python raw string. Handles 8+ URL routing patterns with client-side JSON composition. Not testable in isolation. Changes here affect every page on the static site.

3. **Trends API without response models** — The largest API router has untyped responses. Frontend code and the static site shim both depend on specific field names. A rename in the SQL query silently breaks consumers.

4. **Lesson slug synchronization** — Three independent slug lists with no automated sync check. The next lesson addition is likely to miss one, causing either a broken static site or a gap in test coverage.

5. **Multi-vintage pipeline** — The time-series extraction and loading pipeline is the newest and most complex pipeline. Its test coverage is adequate for happy paths but thin on edge cases (missing years, partial vintage data, schema changes between vintages).

---

## 5. Recommended Next Actions

Execute in this order:

1. **Extract `fetchWithTimeout` to `main.js`** (CR2-01). Removes 50+ lines of duplication across 10 files. Low risk, high cleanup value.

2. **Centralize lesson slugs** (CR2-02). Create `lessons.py` registry. Update `app.py`, `test_lessons.py`, `build_static.py` to import from it. Prevents drift on next lesson addition.

3. **Add Pydantic models to trends API** (CR2-03). Define models in `models.py`, apply to all 7 trends endpoints. Makes the API self-documenting and enables contract tests.

4. **Fix `_table_exists()` exception handling** (CR2-04). Catch specific DuckDB exceptions. Quick fix, prevents masked errors.

5. **Add static site build tests** (CR2-10). Create `tests/test_build_static.py`. This is the highest-value testing improvement available — the static site is the primary deployment with zero coverage.

6. **Add year filter tests for ranked movers** (CR2-11). Quick to write, validates a recent feature.

7. **Add CI step for static site build** (CR2-13). Catches template/API breakage before it reaches production.

8. **Add CSS section comments** (CR2-08). Low effort, improves navigability of a 1,076-line file.

9. **Document static site architecture** (CR2-16). Capture shim URL patterns before they get more complex.

10. **Clean up deploy script** (CR2-17, CR2-18). Add sanity checks, remove dead code.
