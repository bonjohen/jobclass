# Phased Code Review V2 Release Plan

**Source:** `docs/specs/code_review_plan_v2.md` (18 findings, 4 phases)
**Total tasks:** 62
**Estimated phases:** 4

---

## Phase CR2-P1: Foundation and Clarity (16 tasks)

**Goal:** Fix the highest-impact issues — duplicated utilities, lesson slug drift, trends API type safety, and exception handling. These changes reduce maintenance burden and prevent silent failures.

**Entry criteria:** All existing tests pass. Static site builds successfully.
**Exit criteria:** All Phase 1 tasks complete. All tests pass. No regressions in static site.

---

### CR2-01: Extract `fetchWithTimeout` to `main.js`

| # | Task | Status |
|---|------|--------|
| 1 | Add `fetchWithTimeout(url, timeoutMs)` function to `src/jobclass/web/static/js/main.js` with `FETCH_TIMEOUT_MS = 10000` constant | Not Started |
| 2 | Remove local `fetchWithTimeout` definition from `geography_comparison.js`, `hierarchy.js`, `landing.js`, `methodology.js`, `occupation.js` | Not Started |
| 3 | Remove local `fetchWithTimeout` definition from `occupation_comparison.js`, `ranked_movers.js`, `trend_explorer.js`, `trends.js`, `wages.js` | Not Started |
| 4 | Refactor `search.js` to use shared `fetchWithTimeout` with fresh AbortController per call | Not Started |
| 5 | Remove local `FETCH_TIMEOUT_MS` constant from all JS files (now in `main.js`) | Not Started |
| 6 | Run all web tests — verify no regressions | Not Started |
| 7 | Update cache-busting version in `base.html` (bump `?v=` on `main.js`) | Not Started |

---

### CR2-02: Centralize Lesson Slug Registry

| # | Task | Status |
|---|------|--------|
| 8 | Create `src/jobclass/web/lessons.py` with `LESSONS` list of `(slug, title, template_name)` tuples | Not Started |
| 9 | Update `src/jobclass/web/app.py` to import `LESSONS` from `lessons.py` and build `valid_slugs` from it | Not Started |
| 10 | Update `tests/web/test_lessons.py` to import `LESSON_SLUGS` derived from `lessons.py` | Not Started |
| 11 | Update `scripts/build_static.py` to import lesson slugs from `lessons.py` | Not Started |
| 12 | Add test in `test_lessons.py`: verify every registry entry has a corresponding template file on disk | Not Started |
| 13 | Run all tests — verify no regressions | Not Started |

---

### CR2-03: Add Pydantic Response Models to Trends API

| # | Task | Status |
|---|------|--------|
| 14 | Define `TrendSeriesResponse` model in `src/jobclass/web/api/models.py` (fields: soc_code, title, metric, series, years) | Not Started |
| 15 | Define `TrendCompareResponse` model (fields: metric, geo_type, occupations list with series) | Not Started |
| 16 | Define `TrendGeographyResponse` model (fields: soc_code, title, metric, year, areas list) | Not Started |
| 17 | Define `TrendMoversResponse` model (fields: metric, geo_type, year, available_years, gainers, losers) | Not Started |
| 18 | Apply `response_model=` to all 7 endpoints in `src/jobclass/web/api/trends.py` | Not Started |
| 19 | Run all trends tests — verify responses conform to models | Not Started |

---

### CR2-04: Fix `_table_exists()` Exception Handling

| # | Task | Status |
|---|------|--------|
| 20 | Import DuckDB-specific exceptions (`CatalogException`) in `trends.py` | Not Started |
| 21 | Replace bare `except Exception` with `except CatalogException` in `_table_exists()` | Not Started |
| 22 | Add identifier validation (regex or allowlist) for the table name parameter | Not Started |
| 23 | Add test for `_table_exists` with a nonexistent table name | Not Started |

---

## Phase CR2-P2: Correctness and Maintainability (12 tasks)

**Goal:** Address shim error handling, search.js cleanup, CSS organization, and remaining V1 partial fixes.

**Entry criteria:** Phase 1 complete. All tests pass.
**Exit criteria:** All Phase 2 tasks complete. No JavaScript console errors on any page.

---

### CR2-05: Static Site Shim Error Handling

| # | Task | Status |
|---|------|--------|
| 24 | In STATIC_SHIM occupation comparison handler, filter null results from assembled occupations array | Not Started |
| 25 | Add `console.warn()` in shim catch blocks for failed occupation fetches | Not Started |
| 26 | In `occupation_comparison.js`, add null-check before iterating occupation series data | Not Started |
| 27 | Manual test: remove one occupation JSON from `_site/`, verify comparison page degrades gracefully | Not Started |

---

### CR2-06: Fix `search.js` AbortController Reuse

| # | Task | Status |
|---|------|--------|
| 28 | Refactor `search.js` to use `fetchWithTimeout` from `main.js` (depends on CR2-01) | Not Started |
| 29 | Ensure previous request's timeout is cleared before starting new search | Not Started |
| 30 | Run search tests — verify no regressions | Not Started |

---

### CR2-08: Add CSS Section Comments

| # | Task | Status |
|---|------|--------|
| 31 | Add section comment headers to `main.css` for each major section (variables, layout, navigation, cards, search, hierarchy, trends, occupation, wages, lessons, responsive) | Not Started |
| 32 | Audit for repeated magic numbers (border-radius, spacing) — replace 3+ occurrences with CSS variables | Not Started |
| 33 | Visual spot-check: verify all pages render identically after changes | Not Started |

---

### CR2-09: Move Drift Thresholds to Named Constants

| # | Task | Status |
|---|------|--------|
| 34 | Extract drift threshold values in `validate/framework.py` to named constants at module level | Not Started |
| 35 | Add comment explaining rationale for each threshold value | Not Started |
| 36 | Run validation tests — verify no regressions | Not Started |

---

## Phase CR2-P3: Test and Release Confidence (22 tasks)

**Goal:** Close test coverage gaps for new features and add CI verification for the static site.

**Entry criteria:** Phase 2 complete. All tests pass.
**Exit criteria:** All Phase 3 tasks complete. Static site build verified in CI. New feature edge cases covered.

---

### CR2-10: Add Static Site Build Tests

| # | Task | Status |
|---|------|--------|
| 37 | Create `tests/test_build_static.py` test module | Not Started |
| 38 | Test: rendered HTML pages contain the fetch shim `<script>` tag | Not Started |
| 39 | Test: URLs in rendered HTML are rewritten to include base path (`/jobclass`) | Not Started |
| 40 | Test: per-year movers JSON files are generated (at least 2 years) | Not Started |
| 41 | Test: per-metric trend JSON files exist for wage metrics (mean_annual_wage, median_annual_wage) | Not Started |
| 42 | Test: search index JSON is valid and contains occupation entries | Not Started |
| 43 | Test: all lesson pages from registry are generated | Not Started |
| 44 | Test: `_site/.nojekyll` exists in output | Not Started |
| 45 | Test: `_site/static/css/main.css` and `_site/static/js/main.js` are copied | Not Started |

---

### CR2-11: Add Tests for Ranked Movers Year Filter

| # | Task | Status |
|---|------|--------|
| 46 | Test: `/api/trends/movers?year=YYYY` returns data filtered to that year | Not Started |
| 47 | Test: response includes `available_years` list with valid year integers | Not Started |
| 48 | Test: year not in data returns empty gainers/losers (not error) | Not Started |
| 49 | Test: year + metric combination returns consistent results | Not Started |

---

### CR2-12: Add Tests for Trends Comparison Endpoints

| # | Task | Status |
|---|------|--------|
| 50 | Test: occupation comparison with >10 SOC codes returns 400 | Not Started |
| 51 | Test: occupation comparison with invalid SOC code format returns 400 | Not Started |
| 52 | Test: geography comparison with explicit year parameter | Not Started |
| 53 | Test: geography comparison with different metric parameter | Not Started |
| 54 | Test: comparison with occupation that has no time series data | Not Started |

---

### CR2-13: Add CI Step for Static Site Build

| # | Task | Status |
|---|------|--------|
| 55 | Add step to `.github/workflows/ci.yml` that runs `python scripts/build_static.py --base-path /jobclass` | Not Started |
| 56 | Add smoke check: verify `_site/index.html` exists after build | Not Started |
| 57 | Run CI — verify static site step passes on current code | Not Started |

---

### CR2-14: Add Contract Tests for Trends Response Shapes

| # | Task | Status |
|---|------|--------|
| 58 | For each trends endpoint, parse response JSON through Pydantic model and assert no validation errors | Not Started |

---

## Phase CR2-P4: Operational and Reviewer Polish (8 tasks)

**Goal:** Documentation, deploy safety, and long-term maintainability improvements.

**Entry criteria:** Phase 3 complete.
**Exit criteria:** All Phase 4 tasks complete. Documentation accurately reflects current system.

---

### CR2-15: Cache-Busting Documentation

| # | Task | Status |
|---|------|--------|
| 59 | Add cache-busting convention to CLAUDE.md (when and how to update `?v=` parameter) | Not Started |

---

### CR2-16: Document Static Site Architecture

| # | Task | Status |
|---|------|--------|
| 60 | Expand Static Site section in CLAUDE.md with URL pattern → JSON file mapping table and local testing instructions | Not Started |

---

### CR2-17: Add Deploy Script Sanity Checks

| # | Task | Status |
|---|------|--------|
| 61 | Add pre-push assertions in `deploy_pages.py`: verify `_site/index.html`, `_site/static/`, `_site/api/` exist | Not Started |

---

### CR2-18: Remove Redundant Exception Handler

| # | Task | Status |
|---|------|--------|
| 62 | Remove outer `try/except` around `shutil.rmtree(..., ignore_errors=True)` in `deploy_pages.py` | Not Started |

---

## Summary

| Phase | Findings | Tasks | Focus |
|-------|----------|-------|-------|
| CR2-P1 | CR2-01 through CR2-04 | 23 | JS duplication, lesson registry, trends types, exception handling |
| CR2-P2 | CR2-05 through CR2-09 | 13 | Shim errors, search cleanup, CSS, drift thresholds |
| CR2-P3 | CR2-10 through CR2-14 | 22 | Static site tests, year filter tests, comparison tests, CI |
| CR2-P4 | CR2-15 through CR2-18 | 4 | Documentation, deploy safety |
| **Total** | **18 findings** | **62 tasks** | |

---

## Priority Matrix

| Severity | Count | Findings |
|----------|-------|----------|
| Critical | 1 | CR2-10 (static site build tests) |
| High | 3 | CR2-01 (fetchWithTimeout), CR2-02 (lesson slugs), CR2-11 (movers tests) |
| Medium | 7 | CR2-03, CR2-04, CR2-05, CR2-06, CR2-12, CR2-13, CR2-14 |
| Low | 7 | CR2-07, CR2-08, CR2-09, CR2-15, CR2-16, CR2-17, CR2-18 |
