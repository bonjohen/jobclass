# Phased Release Plan — Code Review Remediation

This document is the work-tracking artifact for remediating findings from the code review (`code_review_plan.md`). Each task has a status, traceability to the review finding number, and timestamps updated as work proceeds.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Traces To (code review finding #), Started, Completed

---

## Phase CR1: Foundation and Clarity

Fix issues that block safe execution, clear understanding, or basic trust. Addresses all High-severity security findings and the missing entrypoint problem.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | CR1-01 | Move `escapeHtml()` function from template duplicates into `static/js/main.js` as shared utility | #1 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-02 | Replace `innerHTML` with `textContent` or DOM methods in `templates/landing.html` (spotlight definition) | #1 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-03 | Replace `innerHTML` with escaped DOM construction in `templates/occupation.html` (wages, skills, tasks, projections, similar sections) | #1 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-04 | Escape `soc_code` values in `href` attributes across all templates (breadcrumb, search results, hierarchy links) | #1 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-05 | Add tests that verify HTML characters in API response fields render as text, not executed markup | #1 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-06 | Parameterize `table_name` in `validate/framework.py` information_schema queries (lines 39, 59) using `WHERE table_name = ?` | #2 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-07 | Parameterize table names in source-specific validators (`validate/soc.py:25`, `validate/oews.py:22`, `validate/onet.py:30,51,74,100`) | #2 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-08 | Add allowlist validation for dynamic table names in `load/onet.py:69,119` and `load/oews.py:40` before f-string interpolation | #2 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-09 | Add regex assertion (`^[a-z_]+$`) for table/view names in `web/api/health.py:25,159` before interpolation | #2 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-10 | Add test that crafted table name injection (e.g., `"; DROP TABLE dim_occupation; --"`) is rejected | #2 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-11 | Create `src/jobclass/cli.py` with CLI commands for pipeline operations (run-all, taxonomy-refresh, oews-refresh, onet-refresh, projections-refresh, warehouse-publish) | #5 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-12 | Create `src/jobclass/web/cli.py` with CLI command to start web server (host, port, reload options) | #5 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-13 | Add `[project.scripts]` to `pyproject.toml`: `jobclass-pipeline` and `jobclass-web` entrypoints | #5 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-14 | Document CLI usage in README.md (pipeline commands, web server start) | #5 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-15 | Add `CORSMiddleware` to `web/app.py` with explicit `allowed_origins` defaulting to same-origin | #3 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-16 | Add CSP middleware to `web/app.py` setting `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'` | #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-17 | Add tests verifying CORS rejection of cross-origin requests and CSP header presence | #3, #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-18 | Refactor `config/database.py` to import `DB_PATH` and `MIGRATIONS_DIR` from `config/settings.py` instead of recomputing paths | #6 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR1-19 | Add test verifying `JOBCLASS_DB_PATH` environment variable is respected by both pipeline and web database modules | #6 | 2026-03-23 | 2026-03-23 |

---

## Phase CR2: Correctness and Maintainability

Strengthen code quality, reduce duplication, improve error handling, and make the system more testable and stable. Depends on CR1 for CSP compliance (inline script extraction).

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | CR2-01 | Create `parse/common.py` with unified `SUPPRESSION_MARKERS` set (union of all current markers: `""`, `"*"`, `"**"`, `"#"`, `"-"`, `"--"`, `"N/A"`) | #7 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-02 | Add shared `parse_numeric()`, `parse_float()`, `parse_int()` functions to `parse/common.py` | #7 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-03 | Refactor `parse/oews.py` to import suppression markers and numeric parsers from `parse/common.py` | #7 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-04 | Refactor `parse/onet.py` to import suppression markers and numeric parsers from `parse/common.py` | #7 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-05 | Refactor `parse/projections.py` to import suppression markers and numeric parsers from `parse/common.py` | #7 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-06 | Add `max_length=100` to search query parameter in `web/api/occupations.py` | #8 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-07 | Validate `geo_type` against `Literal["national", "state"]` in `web/api/wages.py`; return 400 for invalid values | #8 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-08 | Validate SOC code format with regex `^\d{2}-\d{4}$` in all endpoints accepting `soc_code`; return 400 for malformed codes | #8 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-09 | Ensure all validation failures return HTTP 400 with `{"error": "bad_request", "message": "..."}` response body | #8 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-10 | Add tests for input validation: oversized search, invalid geo_type, malformed SOC codes all return 400 | #8 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-11 | Add `threading.Lock()` to `web/database.py` around connection initialization in `get_db()` | #9 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-12 | Add concurrent access test: call `get_db()` from multiple threads simultaneously and verify no errors | #9 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-13 | Replace `except Exception: pass` in `extract/orchestrator.py:103` with `except Exception as e: logger.warning(...)` | #10 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-14 | Replace `except Exception: pass` in `web/database.py:38` with specific `except duckdb.Error` and logging | #10 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-15 | Replace `except Exception: pass` in `load/oews.py:62,102` with `except duckdb.CatalogException` for missing tables | #10 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-16 | Verify all exception handlers either log or re-raise; no silent swallowing remains | #10 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-17 | Add `AbortController` to `search.html` to cancel previous in-flight request on new search dispatch | #11 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-18 | Extract inline `<script>` from `templates/landing.html` into `static/js/landing.js` | #4, #11 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-19 | Extract inline `<script>` from `templates/search.html` into `static/js/search.js` | #4, #11 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-20 | Extract inline `<script>` from `templates/hierarchy.html` into `static/js/hierarchy.js` | #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-21 | Extract inline `<script>` from `templates/occupation.html` into `static/js/occupation.js` | #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-22 | Extract inline `<script>` from `templates/wages_comparison.html` into `static/js/wages.js` | #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-23 | Extract inline `<script>` from `templates/methodology.html` into `static/js/methodology.js` | #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-24 | Remove duplicate `escapeHtml()` from all templates; verify all pages reference `main.js` copy | #1, #4 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-25 | Define Pydantic response models for `/api/health`, `/api/metadata`, `/api/stats` endpoints | #26 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-26 | Define Pydantic response models for `/api/occupations/search`, `/api/occupations/hierarchy`, `/api/occupations/{soc_code}` | #26 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-27 | Define Pydantic response models for wages, skills, tasks, similar, projections, methodology endpoints | #26 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-28 | Apply `response_model` parameter to all FastAPI endpoint decorators | #26 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR2-29 | Add contract tests: validate each API response against its Pydantic model | #26 | 2026-03-23 | 2026-03-23 |

---

## Phase CR3: Test and Release Confidence

Strengthen tests, add CI/CD, improve release validation, and close coverage gaps. Depends on CR2 for input validation (negative tests require 400 responses to exist).

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | CR3-01 | Replace `assert len(...) > 0` with exact expected counts in pipeline parser tests (`test_soc_parser.py`, `test_oews_parser.py`, `test_onet_parser.py`) | #12 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-02 | Replace `assert > 0` with exact counts in pipeline integration tests (`test_orchestration.py`, `test_marts.py`, `test_end_to_end.py`) | #12 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-03 | Replace `is not None` assertions with specific value checks in web API tests (all `test_w*.py` files) | #12 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-04 | Add `TestInvalidInput` class to web tests: invalid SOC codes (`"15-XXXX"`, `"99-9999"`, empty string, too short/long) | #13 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-05 | Add negative tests for invalid `geo_type` parameter and oversized search queries (>100 chars) | #13 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-06 | Add negative tests for empty result sets: search with no matches, occupation with no wages/skills/projections | #13 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-07 | Add parser edge-case tests: empty source files, header-only files, files with unexpected encoding | #13 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-08 | Add test for database connection failure path (verify health endpoint returns 503) | #13 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-09 | Create independent `soc_only_db` fixture that loads only SOC data (no OEWS or O\*NET) | #14 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-10 | Create independent `oews_only_db` fixture that loads SOC + OEWS only (no O\*NET) | #14 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-11 | Create independent `onet_only_db` fixture that loads SOC + O\*NET only (no OEWS) | #14 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-12 | Refactor SOC-specific tests to use `soc_only_db`; verify they pass without OEWS/O\*NET loading | #14 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-13 | Create `.github/workflows/ci.yml` with: checkout, Python setup, dependency install, ruff lint+format, pytest | #15 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-14 | Add Python version matrix (3.11, 3.12) to CI workflow | #15 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-15 | Add coverage reporting to CI (`--cov=jobclass --cov-report=xml`) with coverage upload step | #15 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-16 | Add CI status badge to README.md | #15 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-17 | Generate `requirements.lock` using `pip-compile pyproject.toml -o requirements.lock` | #17 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-18 | Generate `requirements-dev.lock` for development dependencies | #17 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-19 | Add CI step that installs from lock file and verifies tests pass | #17 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-20 | Create `Dockerfile` with multi-stage build: install deps from lock file, copy source, run uvicorn | #16 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-21 | Create `docker-compose.yml` with web service mounting `warehouse.duckdb` via volume | #16 | 2026-03-23 | 2026-03-23 |
| `[X]` | CR3-22 | Add container build and run instructions to README.md; verify `docker build .` and health check from container | #16 | 2026-03-23 | 2026-03-23 |

---

## Phase CR4: Operational and Reviewer Polish

Improve observability, developer experience, documentation, and trust artifacts. Depends on CR3 for Dockerfile (operational docs reference container deployment).

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | CR4-01 | Add `limit` (default 50, max 200) and `offset` (default 0) query parameters to search endpoint | #18 | | |
| `[ ]` | CR4-02 | Add `limit` and `offset` query parameters to state-level wages endpoint | #18 | | |
| `[ ]` | CR4-03 | Return pagination metadata in search and wages responses: `{"results": [...], "total": N, "limit": N, "offset": N}` | #18 | | |
| `[ ]` | CR4-04 | Add pagination tests: verify limit, offset, total count accuracy | #18 | | |
| `[ ]` | CR4-05 | Add `role="region" aria-live="polite"` to all dynamically loaded content sections in `occupation.html` | #19 | | |
| `[ ]` | CR4-06 | Add `aria-live="polite"` to `wages_comparison.html` table container | #19 | | |
| `[ ]` | CR4-07 | Add `aria-busy="true"` during loading and `aria-busy="false"` when content is ready on all dynamic sections | #19 | | |
| `[ ]` | CR4-08 | Add keyboard event handlers (arrow keys, Enter, Space) for hierarchy tree navigation | #19 | | |
| `[ ]` | CR4-09 | Change `autocomplete="off"` to `autocomplete="search"` in `search.html` | #19 | | |
| `[ ]` | CR4-10 | Add `AbortController` with 10-second timeout to all fetch calls in external JS files | #20 | | |
| `[ ]` | CR4-11 | Add error state UI (user-visible message) for every dynamically loaded section on fetch failure | #20 | | |
| `[ ]` | CR4-12 | Add tests verifying fetch timeout triggers error message display | #20 | | |
| `[ ]` | CR4-13 | Add version query parameter to static asset URLs in `base.html` (e.g., `/static/css/main.css?v=CR1`) | #21 | | |
| `[ ]` | CR4-14 | Add `SELECT 1` connectivity check at start of `/api/health` endpoint; return 503 on failure | #22 | | |
| `[ ]` | CR4-15 | Add migration state check to `/api/health`; verify all expected migrations are applied | #22 | | |
| `[ ]` | CR4-16 | Add `/api/ready` readiness probe endpoint (separate from liveness health check) | #22 | | |
| `[ ]` | CR4-17 | Add tests: health returns 503 when database is unavailable; health returns 503 when migrations incomplete | #22 | | |
| `[ ]` | CR4-18 | Add "Quick Start" section to README.md: dev setup, running tests, starting web app, running pipeline | #23 | | |
| `[ ]` | CR4-19 | Add "Deployment" section to README.md: environment variables, container build, data directory requirements | #23 | | |
| `[ ]` | CR4-20 | Add "Operations" section to README.md: monitoring, backup, recovery, common troubleshooting | #23 | | |
| `[ ]` | CR4-21 | Create `.env.example` documenting all environment variables with descriptions and defaults | #23 | | |
| `[ ]` | CR4-22 | Add `prometheus_client` dependency; create pipeline run counters and duration histograms | #24 | | |
| `[ ]` | CR4-23 | Add `/metrics` endpoint to web app exposing Prometheus-formatted request metrics | #24 | | |
| `[ ]` | CR4-24 | Add tests verifying `/metrics` returns valid Prometheus output and pipeline runs increment counters | #24 | | |
| `[ ]` | CR4-25 | Extract hardcoded drift thresholds (`20.0%`, `15.0%` in `validate/framework.py`) into named constants with documentation | #25 | | |

---

## Phase Summary

| Phase | Description | Task Count | Dependencies |
|-------|-------------|------------|--------------|
| CR1 | Foundation and Clarity — security fixes, entrypoints, config | 19 | None |
| CR2 | Correctness and Maintainability — duplication, validation, error handling, script extraction, typed APIs | 29 | CR1 (CSP compliance requires CR1-16) |
| CR3 | Test and Release Confidence — assertion quality, negative tests, fixture isolation, CI/CD, containerization | 22 | CR2 (negative tests require input validation from CR2-06 through CR2-09) |
| CR4 | Operational and Reviewer Polish — pagination, accessibility, timeouts, health checks, docs, metrics | 25 | CR3 (operational docs reference Dockerfile from CR3-20) |
| **Total** | | **95** | |

---

## Dependency Graph

```
Phase CR1 (Foundation) ──► Phase CR2 (Correctness) ──► Phase CR3 (Test Confidence) ──► Phase CR4 (Polish)
     │                          │                            │
     ├─ XSS fixes               ├─ Parser consolidation      ├─ Assertion strengthening
     ├─ SQL injection fixes      ├─ Input validation          ├─ Negative tests
     ├─ CLI entrypoints          ├─ Exception handling        ├─ Fixture isolation
     ├─ CORS/CSP headers         ├─ Script extraction         ├─ CI/CD pipeline
     └─ Config consolidation     ├─ Search race condition     ├─ Lock file
                                 └─ Pydantic response models  ├─ Dockerfile
                                                              └─ Container docs
```

Phases are sequential. CR2 depends on CR1 because script extraction (CR2-18 through CR2-24) must follow CSP middleware (CR1-16). CR3 depends on CR2 because negative tests (CR3-04 through CR3-06) require input validation (CR2-06 through CR2-09) to exist. CR4 depends on CR3 because operational documentation (CR4-18 through CR4-20) references the Dockerfile (CR3-20) and CI workflow (CR3-13).

---

## Traceability Matrix

Maps code review finding numbers to the tasks that address them.

| Finding # | Title | Severity | Tasks |
|-----------|-------|----------|-------|
| #1 | XSS via innerHTML | High | CR1-01, CR1-02, CR1-03, CR1-04, CR1-05, CR2-24 |
| #2 | SQL injection via f-string table names | High | CR1-06, CR1-07, CR1-08, CR1-09, CR1-10 |
| #3 | No CORS middleware | High | CR1-15, CR1-17 |
| #4 | No CSP header | Medium | CR1-16, CR1-17, CR2-18 through CR2-24 |
| #5 | No CLI entrypoints | High | CR1-11, CR1-12, CR1-13, CR1-14 |
| #6 | Config path duplication | Low | CR1-18, CR1-19 |
| #7 | Parser utility duplication | Medium | CR2-01, CR2-02, CR2-03, CR2-04, CR2-05 |
| #8 | No input validation on API | Medium | CR2-06, CR2-07, CR2-08, CR2-09, CR2-10 |
| #9 | Thread-unsafe connection init | Low | CR2-11, CR2-12 |
| #10 | Broad exception swallowing | Low | CR2-13, CR2-14, CR2-15, CR2-16 |
| #11 | Search race condition | Medium | CR2-17, CR2-18, CR2-19 |
| #12 | Vague test assertions | Medium | CR3-01, CR3-02, CR3-03 |
| #13 | No negative tests | High | CR3-04, CR3-05, CR3-06, CR3-07, CR3-08 |
| #14 | Deep fixture chains | Medium | CR3-09, CR3-10, CR3-11, CR3-12 |
| #15 | No CI/CD | High | CR3-13, CR3-14, CR3-15, CR3-16 |
| #16 | No Dockerfile | High | CR3-20, CR3-21, CR3-22 |
| #17 | No dependency lock file | Medium | CR3-17, CR3-18, CR3-19 |
| #18 | No API pagination | Medium | CR4-01, CR4-02, CR4-03, CR4-04 |
| #19 | Missing aria-live regions | Low | CR4-05, CR4-06, CR4-07, CR4-08, CR4-09 |
| #20 | No fetch timeouts | Low | CR4-10, CR4-11, CR4-12 |
| #21 | No static cache-busting | Low | CR4-13 |
| #22 | Weak health endpoint | Low | CR4-14, CR4-15, CR4-16, CR4-17 |
| #23 | No operational documentation | Medium | CR4-18, CR4-19, CR4-20, CR4-21 |
| #24 | No metrics export | Low | CR4-22, CR4-23, CR4-24 |
| #25 | Hardcoded magic numbers | Low | CR4-25 |
| #26 | Missing API versioning | Low | CR2-25, CR2-26, CR2-27, CR2-28, CR2-29 |
