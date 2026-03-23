# Code Review — Phased Remediation Plan

## 1. Executive Summary

The JobClass codebase is architecturally sound with clean four-layer separation, comprehensive testing (376 tests), and good observability for the pipeline layer. The design is well-documented and the implementation follows its own stated conventions with few exceptions.

The most important concerns, in priority order:

1. **XSS vulnerabilities in the web frontend.** Multiple templates use `innerHTML` with unescaped API response data. An attacker who controls occupation definitions or source metadata could inject scripts. This is the only finding that could cause direct harm to users.

2. **No deployment infrastructure.** No Dockerfile, no CI/CD, no CLI entrypoints, no deployment scripts, no dependency lock file. The project cannot be reliably deployed outside the developer's machine without manual intervention.

3. **Shallow test depth despite high test count.** 31 assertions use `> 0` instead of exact values. No negative tests for invalid input, no edge-case tests for empty results, no property-based testing. The test suite catches regressions but does not prove correctness at boundaries.

4. **No input validation on web API endpoints.** Search queries have no length limit, `geo_type` is not validated against an enum, SOC codes are not format-checked. Combined with missing CORS and CSP headers, the API is unprotected.

5. **Code duplication across parsers.** Suppression marker sets and numeric parsing functions are copy-pasted across three parser modules. A fourth data source would require copying them again.

---

## 2. Project Shape as Observed

**System type:** Batch ETL data pipeline feeding a read-only analytical warehouse, with a FastAPI web application for human consumption.

**Major parts:**
- **Extract layer** (`extract/`): Manifest-driven download with retry, checksum, and immutable raw storage.
- **Parse layer** (`parse/`): Source-specific parsers (SOC, OEWS, O\*NET, Projections) producing typed dataclasses.
- **Load layer** (`load/`): Idempotent staging and warehouse loaders with dimension conformance.
- **Validate layer** (`validate/`): Reusable framework validators (structural, grain, referential, temporal, drift) plus source-specific validation modules.
- **Orchestrate layer** (`orchestrate/`): Five pipeline functions (`taxonomy_refresh`, `oews_refresh`, `onet_refresh`, `projections_refresh`, `warehouse_publish`) with dependency gating and run manifesting.
- **Observe layer** (`observe/`): Structured JSON logging, run manifest tracking, row-count delta reporting, schema drift detection.
- **Marts layer** (`marts/`): Five analyst-facing SQL views.
- **Web layer** (`web/`): FastAPI app with 6 API routers, 6 HTML page routes, Jinja2 templates with client-side fetch for data loading.
- **Config** (`config/`): Settings with environment variable overrides, DuckDB connection management, SQL migrations.

**Workflow:** Extract (download) -> Parse (source-specific) -> Validate (structural + semantic) -> Load (idempotent staging then warehouse) -> Publish (marts). Web layer reads warehouse in read-only mode.

**Boundaries:** Clean. Web layer imports only from `web.database`, never from pipeline modules. Pipeline modules import downward (orchestrate -> load -> parse, orchestrate -> validate). Observe is cross-cutting. Config is the lowest layer.

---

## 3. Phased Release Plan

### Phase 1: Foundation and Clarity

**Goal:** Fix issues that block safe execution, clear understanding, or basic trust.

#### 1.1 — XSS Vulnerabilities in Templates

**Deficiency:** Multiple templates insert API response data into the DOM via `innerHTML` without escaping. Affected locations:
- `templates/landing.html:55` — Occupation definition inserted via `innerHTML`.
- `templates/occupation.html:171` — `source_release_id` and `reference_period` concatenated into HTML string.
- `templates/occupation.html:189` — `source_version` concatenated into HTML string.
- `templates/occupation.html:208,230` — `projection_cycle` and `source_release_id` concatenated into HTML string.
- `templates/occupation.html:109` — `soc_code` used in `href` attribute without escaping.

**Why Phase 1:** XSS is a direct security risk. If any API response value contains HTML or script tags, it executes in the user's browser. Even though the data comes from federal sources today, the pattern is unsafe by default.

**Recommended changes:**
- Replace all `innerHTML` assignments that include API data with DOM methods (`textContent`, `createElement`, `setAttribute`).
- Move the `escapeHtml()` function (currently duplicated in 4 templates) into `static/js/main.js` and use it everywhere API data touches HTML.
- Escape `soc_code` values used in `href` attributes.

**Recommended validation:**
- Add tests that verify API responses with HTML characters (e.g., `<script>`, `"onload=`) are rendered as text, not executed.
- Test breadcrumb rendering with SOC codes containing special characters.

**Expected outcome:** No unescaped API data reaches the DOM in any template.

---

#### 1.2 — SQL Injection via f-string Table Names

**Deficiency:** Table and column names are interpolated into SQL queries via f-strings in multiple locations:
- `validate/framework.py:39,59` — `f"... WHERE table_name = '{table_name}'"` in information_schema queries.
- `validate/soc.py:25`, `validate/oews.py:22`, `validate/onet.py:30,51,74,100` — Same pattern.
- `load/onet.py:69,119` — `f"INSERT INTO {table_name}..."`.
- `load/oews.py:40` — `f"DELETE FROM {table_name}..."`.
- `web/api/health.py:25,159` — `f"SELECT COUNT(*) FROM {t}"` and `f"SELECT COUNT(*) FROM {view}"`.

**Why Phase 1:** While table names are currently hardcoded in calling code, this pattern is unsafe by default. A future change that passes user-influenced data to these functions would create an exploitable injection point.

**Recommended changes:**
- For information_schema queries: use parameterized `WHERE table_name = ?` (DuckDB supports this).
- For DML with dynamic table names: validate against an explicit allowlist before interpolation, or use DuckDB's `sql_identifier()` escaping.
- For `health.py`: the table list is already hardcoded; add an assertion that table names match `^[a-z_]+$` before interpolation.

**Recommended validation:**
- Add a test that attempts SQL injection via a crafted table name (e.g., `"; DROP TABLE dim_occupation; --"`) and verifies it fails safely.

**Expected outcome:** No SQL query accepts unvalidated identifiers from parameters.

---

#### 1.3 — Missing CLI Entrypoints

**Deficiency:** There is no way to run the pipeline or web app from the command line. No `__main__.py`, no `console_scripts` in `pyproject.toml`, no shell scripts. A user must open a Python REPL and call functions manually.

**Why Phase 1:** Without clear entrypoints, the project cannot be executed by someone who didn't write it. This blocks deployment, CI/CD, and onboarding.

**Recommended changes:**
- Add `[project.scripts]` to `pyproject.toml` with two entrypoints: `jobclass-web` (starts uvicorn) and `jobclass-pipeline` (runs pipeline orchestration).
- Create `src/jobclass/web/cli.py` with a CLI command to start the web server.
- Create `src/jobclass/cli.py` with CLI commands for pipeline operations (e.g., `jobclass-pipeline run-all`, `jobclass-pipeline taxonomy-refresh`).
- Document both entrypoints in README.md.

**Recommended validation:**
- Verify `pip install -e .` creates working `jobclass-web` and `jobclass-pipeline` commands.
- Verify `jobclass-web --help` and `jobclass-pipeline --help` produce usage information.

**Expected outcome:** The project is runnable from the command line without Python REPL knowledge.

---

#### 1.4 — Missing Web Security Headers

**Deficiency:**
- No CORS middleware configured in `app.py`. Any website can call the API.
- No Content Security Policy header. Inline scripts execute without restriction.
- No rate limiting. The API accepts unlimited requests per client.

**Why Phase 1:** These are baseline security measures that should exist before any deployment.

**Recommended changes:**
- Add `CORSMiddleware` to `app.py` with explicit `allowed_origins` (default to same-origin only).
- Add CSP header via middleware: `default-src 'self'; script-src 'self'; style-src 'self'`.
- Move all inline `<script>` content from templates into external `.js` files in `static/js/` to comply with CSP.
- Consider adding `slowapi` or similar for rate limiting.

**Recommended validation:**
- Test that cross-origin requests are rejected.
- Test that inline script injection via CSP violation is blocked.

**Expected outcome:** Web application has defense-in-depth security headers.

---

#### 1.5 — Configuration Drift Between database.py and settings.py

**Deficiency:** `config/database.py:7-8` defines default paths locally (`_MIGRATIONS_DIR`, `DEFAULT_DB_PATH`) by computing `Path(__file__).parent.parent.parent.parent / "..."` instead of importing from `settings.py`, which already defines these paths via environment variable overrides.

**Why Phase 1:** Two sources of truth for the same paths. If someone changes the default in `settings.py`, `database.py` still uses its own default.

**Recommended changes:**
- Change `config/database.py` to import `DB_PATH` and `MIGRATIONS_DIR` from `settings.py`.

**Recommended validation:**
- Verify that setting `JOBCLASS_DB_PATH` environment variable is respected by both pipeline and web layers.

**Expected outcome:** Single source of truth for all path configuration.

---

### Phase 2: Correctness and Maintainability

**Goal:** Strengthen code quality, reduce duplication, improve error handling, and make the system more testable and stable.

#### 2.1 — Consolidate Duplicated Parser Utilities

**Deficiency:** Suppression marker sets and numeric parsing functions are duplicated across three parser modules:
- `parse/oews.py:10` — `SUPPRESSION_MARKERS = {"**", "#", "N/A", "*", "-", ""}`
- `parse/onet.py:52` — `("", "N/A", "*", "**", "#")` (inline tuple, different order)
- `parse/projections.py:34` — `("", "--", "N/A", "#", "**", "*")` (includes `"--"`)

Numeric parsing (`_parse_numeric`, `_parse_float`, `_parse_int`) is independently implemented in all three modules with slightly different marker handling.

**Why Phase 2:** Duplication increases the risk of inconsistent null handling across data sources. Adding a new source requires copying and adapting these functions.

**Recommended changes:**
- Create `parse/common.py` with a unified `SUPPRESSION_MARKERS` set and shared `parse_numeric()`, `parse_float()`, `parse_int()` functions.
- Import from `common.py` in all parser modules.
- Ensure the unified set is the union of all current marker sets.

**Recommended validation:**
- Existing parser tests must continue passing without modification.
- Add a test that each parser module imports from `common.py` (not a local copy).

**Expected outcome:** Single authoritative definition of suppression markers and numeric parsing.

---

#### 2.2 — Add Input Validation to Web API Endpoints

**Deficiency:** No API endpoint validates its input:
- `occupations.py:13` — Search query `q` has no max length. A 10 MB string would be passed to SQL ILIKE.
- `wages.py:15` — `geo_type` parameter is not validated against allowed values (`national`, `state`). Invalid values silently return empty results.
- `skills.py`, `projections.py`, `occupations.py` — SOC code format is not validated. Malformed codes produce 404 or empty results with no explanation.

**Why Phase 2:** Without validation, the API is fragile and gives confusing responses. Consumers cannot distinguish "no data" from "invalid request."

**Recommended changes:**
- Add `max_length=100` to the search query parameter.
- Validate `geo_type` against a `Literal["national", "state"]` type or raise 400.
- Validate SOC code format (regex `^\d{2}-\d{4}$`) or raise 400 with a clear message.
- Return 400 (not 404 or empty 200) for malformed input.

**Recommended validation:**
- Test that oversized search queries return 400.
- Test that invalid `geo_type` returns 400.
- Test that malformed SOC codes return 400 with error details.

**Expected outcome:** API rejects invalid input with clear error messages.

---

#### 2.3 — Thread Safety for Web Database Connection

**Deficiency:** `web/database.py:11-28` uses a module-level `_conn` global with no synchronization. The check-then-set between `if _conn is not None` (line 21) and `_conn = duckdb.connect(...)` (line 28) is a TOCTOU race condition under concurrent requests.

**Why Phase 2:** While the practical impact is low (DuckDB connections are cheap, read-only, and the race window is small), the pattern is incorrect and could cause subtle bugs under load.

**Recommended changes:**
- Add `threading.Lock()` around the connection initialization in `get_db()`.
- Alternatively, use FastAPI's dependency injection with `Depends()` for connection management.

**Recommended validation:**
- Add a concurrent access test that calls `get_db()` from multiple threads simultaneously.

**Expected outcome:** Connection initialization is thread-safe.

---

#### 2.4 — Improve Exception Handling Specificity

**Deficiency:** Several exception handlers catch `Exception` broadly and swallow errors silently:
- `extract/orchestrator.py:103` — `except Exception: pass` when run_manifest creation fails.
- `web/database.py:38-39` — `except Exception: pass` on connection close.
- `load/oews.py:62,102` — `except Exception: pass` when staging table doesn't exist.

**Why Phase 2:** Silent exception swallowing hides failures. When something goes wrong in production, these locations produce no diagnostic output.

**Recommended changes:**
- Replace `except Exception: pass` with specific exception types (e.g., `duckdb.CatalogException` for missing tables).
- Add `logger.debug()` or `logger.warning()` in each catch block so failures are visible in logs.
- In `orchestrator.py:103`, log the nested failure at WARNING level.

**Recommended validation:**
- Verify that expected exception types are caught correctly.
- Verify that unexpected exceptions propagate (not swallowed).

**Expected outcome:** No silent exception swallowing; all catch blocks either log or re-raise.

---

#### 2.5 — Fix Search Race Condition

**Deficiency:** `templates/search.html:31-51` implements debounced search with `setTimeout` but does not track in-flight requests. If two searches are dispatched and the second response arrives before the first, the UI displays stale results.

**Why Phase 2:** Users typing quickly see results from a previous query, creating confusion.

**Recommended changes:**
- Add a request counter or `AbortController` to cancel previous in-flight requests when a new search is dispatched.
- On response, check that the response corresponds to the current query before updating the DOM.

**Recommended validation:**
- Manual test: type rapidly, verify results always match the current search input.

**Expected outcome:** Search results always correspond to the current query text.

---

#### 2.6 — Consolidate escapeHtml and Inline Scripts

**Deficiency:** The `escapeHtml()` function is duplicated identically in 4 templates:
- `search.html:53-57`
- `hierarchy.html:62-66`
- `occupation.html:256-260`
- `wages_comparison.html:54-58`

All substantial JavaScript is inline in `<script>` tags within templates (6 templates total), making it untestable and incompatible with CSP.

**Why Phase 2:** Duplication increases maintenance burden. Inline scripts block CSP enforcement (Phase 1.4).

**Recommended changes:**
- Move `escapeHtml()` to `static/js/main.js`.
- Extract each template's inline script into a dedicated `.js` file (e.g., `static/js/search.js`, `static/js/hierarchy.js`, etc.).
- Load via `<script src="/static/js/search.js"></script>` in templates.

**Recommended validation:**
- All existing web tests continue passing.
- CSP header can be set to `script-src 'self'` without breaking functionality.

**Expected outcome:** Zero inline scripts; all JavaScript in external files.

---

#### 2.7 — Add API Response Type Definitions

**Deficiency:** All API endpoints return `-> dict` without typed schemas. API consumers must infer response shapes from runtime behavior or test expectations.

**Why Phase 2:** Untyped API responses make contract testing impossible and increase the risk of breaking changes going undetected.

**Recommended changes:**
- Define Pydantic response models (or TypedDict classes) for each endpoint.
- Use FastAPI's `response_model` parameter to enforce schemas.

**Recommended validation:**
- Existing API tests continue passing.
- Add a contract test that validates each response against its Pydantic model.

**Expected outcome:** All API endpoints have typed, documented response schemas.

---

### Phase 3: Test and Release Confidence

**Goal:** Strengthen tests, add CI/CD, improve release validation, and close coverage gaps.

#### 3.1 — Replace Vague Assertions with Exact Values

**Deficiency:** 31 assertions across the test suite use `assert len(x) > 0` or `assert count > 0` instead of checking exact expected values. Examples:
- `test_soc_parser.py:12` — `assert len(majors) >= 1`
- `test_marts.py:37` — `assert len(rows) > 0`
- `test_orchestration.py:31` — `assert dim_count > 0`
- Multiple web tests check `is not None` without validating values.

**Why Phase 3:** These tests pass even when wrong data is loaded. They catch complete failures but not partial corruption or off-by-one errors.

**Recommended changes:**
- Replace each `> 0` assertion with the exact expected count from the fixture.
- Replace `is not None` assertions with specific value checks where the fixture data is known.
- Document the expected counts as comments referencing the fixture file.

**Recommended validation:**
- Intentionally break a fixture (e.g., remove one row) and verify the test fails with a clear message.

**Expected outcome:** Tests prove specific expected outcomes, not just non-emptiness.

---

#### 3.2 — Add Negative and Edge-Case Tests

**Deficiency:** The test suite has almost no negative tests. Missing coverage includes:
- Invalid SOC codes (e.g., `"15-XXXX"`, `"99-9999"`, empty string).
- Empty search results (query with no matches).
- Occupation with no wages, no skills, or no projections.
- Malformed source files (empty files, files with only headers, encoding issues).
- Invalid `geo_type` parameter values.
- Database connection failures.
- Version misalignment (e.g., 2020 SOC data with 2018 version label).

**Why Phase 3:** Negative tests validate error paths. Without them, error handling code is untested and may fail silently or crash in production.

**Recommended changes:**
- Add a `TestInvalidInput` class to each web test module with tests for malformed requests.
- Add parser tests for empty files, header-only files, and files with unexpected encoding.
- Add API tests for nonexistent occupations, invalid geo_type, and oversized queries.
- Add at least one test per API endpoint for the 400 error path.

**Recommended validation:**
- Each new test should fail if the corresponding validation code is removed.

**Expected outcome:** Every error path in the codebase has at least one test.

---

#### 3.3 — Break Apart Fixture Dependency Chains

**Deficiency:** Test fixtures form a deep chain: `onet_loaded_db` depends on `oews_loaded_db` depends on `soc_loaded_db` depends on `migrated_db`. A simple SOC parser test loads the entire O\*NET dataset. This slows the suite and creates cascading failures.

**Why Phase 3:** Slow fixtures discourage running tests. Deep chains mean a single fixture bug breaks hundreds of tests.

**Recommended changes:**
- Create independent fixtures for each data source layer: `soc_only_db`, `oews_only_db`, `onet_only_db`.
- Use the full chain only for integration and E2E tests.
- Parameterize version-specific fixtures (test with multiple SOC versions, OEWS releases).

**Recommended validation:**
- Verify that SOC-only tests run without loading OEWS or O\*NET data.
- Verify that the full suite still passes with the restructured fixtures.

**Expected outcome:** Unit tests are fast and isolated; integration tests use full fixtures.

---

#### 3.4 — Add CI/CD Pipeline

**Deficiency:** No CI/CD configuration exists. No GitHub Actions, Jenkinsfile, or any automation. Ruff is configured in `pyproject.toml` but not enforced. Test coverage is not tracked.

**Why Phase 3:** Without CI/CD, code quality is enforced only by developer discipline. Regressions can be merged without detection.

**Recommended changes:**
- Create `.github/workflows/ci.yml` with:
  - Python matrix (3.11, 3.12).
  - Install dependencies (`pip install -e ".[dev]"`).
  - Run ruff lint and format check.
  - Run pytest with coverage (`--cov=jobclass --cov-report=xml`).
  - Upload coverage report.
- Add a status badge to README.md.

**Recommended validation:**
- Push a branch with a deliberate test failure; verify CI fails.
- Push a branch with a ruff violation; verify CI fails.

**Expected outcome:** Every push and PR is automatically tested and linted.

---

#### 3.5 — Add Dependency Lock File

**Deficiency:** No lock file (`requirements.lock`, `Pipfile.lock`, or `poetry.lock`). Dependencies use `>=` lower bounds with no upper constraints. Two installations at different times may resolve different transitive dependency versions.

**Why Phase 3:** Without a lock file, builds are not reproducible. A new release of any transitive dependency could break the project.

**Recommended changes:**
- Generate `requirements.lock` using `pip-compile pyproject.toml -o requirements.lock`.
- Generate `requirements-dev.lock` for development dependencies.
- Add a CI step that installs from lock file and runs tests.
- Document the lock file regeneration process.

**Recommended validation:**
- Verify that `pip install -r requirements.lock` produces a working installation.
- Verify that CI uses the lock file for reproducible builds.

**Expected outcome:** Reproducible installations across environments and time.

---

#### 3.6 — Add Containerization

**Deficiency:** No Dockerfile or docker-compose.yml. The application can only run on the developer's machine with manually installed dependencies.

**Why Phase 3:** Containerization is required for deployment to any modern infrastructure.

**Recommended changes:**
- Create `Dockerfile` for the web application (multi-stage build: install deps, copy source, run uvicorn).
- Create `docker-compose.yml` with a single service (web app reads local `warehouse.duckdb` via volume mount).
- Document container build and run in README.md.

**Recommended validation:**
- `docker build .` succeeds.
- `docker-compose up` starts the web app and serves the landing page.
- Health endpoint returns 200 from within the container.

**Expected outcome:** The application is deployable as a container.

---

### Phase 4: Operational and Reviewer Polish

**Goal:** Improve observability, developer experience, documentation, and trust artifacts.

#### 4.1 — Add Pagination to API Endpoints

**Deficiency:** Search, hierarchy, and wages endpoints return unbounded result sets:
- `occupations.py:20-29` — `search_occupations()` returns all matching results.
- `occupations.py:45-76` — `occupation_hierarchy()` returns the entire tree.
- `wages.py:28-41` — `occupation_wages()` returns all state-level rows.

**Why Phase 4:** With the current dataset size (840 occupations, 56 geographies), performance is acceptable. But the pattern is not scalable, and a reviewer would flag it.

**Recommended changes:**
- Add `limit` (default 50, max 200) and `offset` (default 0) query parameters to search and wages endpoints.
- Return pagination metadata: `{"results": [...], "total": 150, "limit": 50, "offset": 0}`.
- Hierarchy endpoint can remain unbounded (tree structure is fixed-size by definition).

**Recommended validation:**
- Test that `limit=5` returns exactly 5 results.
- Test that `offset=5` skips the first 5 results.
- Test that total count is accurate regardless of limit/offset.

**Expected outcome:** API endpoints are scalable and self-documenting.

---

#### 4.2 — Add Missing aria-live Regions and Accessibility Improvements

**Deficiency:**
- Dynamic content sections in `occupation.html` and `wages_comparison.html` lack `aria-live` attributes. Screen readers do not announce content changes.
- Hierarchy tree uses ARIA tree roles but lacks keyboard navigation (arrow keys, Enter, Space).
- `search.html` has `autocomplete="off"`, which is discouraged by modern standards.

**Why Phase 4:** Accessibility is a quality attribute that affects trust and compliance. Current implementation has ARIA landmarks but incomplete interaction patterns.

**Recommended changes:**
- Add `role="region" aria-live="polite"` to all dynamically loaded content sections.
- Set `aria-busy="true"` during loading, `"false"` when content is ready.
- Add keyboard event handlers for tree navigation (arrow keys to expand/collapse).
- Change `autocomplete="off"` to `autocomplete="search"`.

**Recommended validation:**
- Test with a screen reader (VoiceOver or NVDA) that content changes are announced.
- Test that tree can be navigated entirely via keyboard.

**Expected outcome:** Application meets WCAG 2.1 AA for dynamic content.

---

#### 4.3 — Add Fetch Timeouts and Error States

**Deficiency:** All 7 templates with fetch calls (landing, search, hierarchy, occupation, wages_comparison, methodology) have no request timeout. If the server hangs, the browser waits indefinitely. Some fetch calls have no error handling at all (landing.html stats fetch).

**Why Phase 4:** Users should see an error message within seconds, not wait indefinitely.

**Recommended changes:**
- Add `AbortController` with a 10-second timeout to all fetch calls.
- Add error state UI for every dynamically loaded section (not just "Loading...").
- Ensure all fetch chains have `.catch()` handlers that display user-visible error messages.

**Recommended validation:**
- Test that a 10-second timeout triggers an error message.
- Test that fetch errors display an error state in the UI.

**Expected outcome:** Every fetch call has a timeout and a visible error state.

---

#### 4.4 — Add Static Asset Cache-Busting

**Deficiency:** CSS and JS are referenced by hardcoded filenames (`/static/css/main.css`, `/static/js/main.js`). When files are updated, browsers with cached versions see stale assets.

**Why Phase 4:** Stale CSS/JS causes visual bugs and broken functionality after deployments.

**Recommended changes:**
- Add a version query parameter to static asset URLs (e.g., `/static/css/main.css?v=W9`).
- Alternatively, implement content hashing in filenames during build.

**Recommended validation:**
- Verify that changing a CSS rule and updating the version parameter causes browsers to fetch the new file.

**Expected outcome:** Asset updates are visible to users without manual cache clearing.

---

#### 4.5 — Strengthen Health Endpoint for Production

**Deficiency:** The health endpoint (`/api/health`) queries table counts but does not verify database connectivity separately, does not check migration state, and has no readiness/liveness distinction.

**Why Phase 4:** Production health checks should distinguish "database is reachable" from "application is ready to serve traffic."

**Recommended changes:**
- Add a `SELECT 1` connectivity check at the start of the health endpoint.
- Add a check that all expected migrations are applied.
- Return 503 with details if connectivity fails or migrations are missing.
- Consider adding a separate `/api/ready` endpoint for readiness probes.

**Recommended validation:**
- Test that health returns 503 when the database is unavailable.
- Test that health returns 503 when migrations are incomplete.

**Expected outcome:** Health endpoint is production-ready for load balancer integration.

---

#### 4.6 — Add Operational Documentation

**Deficiency:** README.md documents architecture and test results but not operations:
- No instructions for running the pipeline or web app.
- No instructions for downloading source data.
- No backup or recovery guidance.
- No monitoring or alerting guidance.
- No runbook for common failures.

**Why Phase 4:** A project that cannot be operated by someone who didn't write it is not production-ready.

**Recommended changes:**
- Add a "Quick Start" section to README.md: development setup, running the pipeline, running the web app.
- Add a "Deployment" section: environment variables, container build, data directory requirements.
- Add a "Operations" section: monitoring, backup, recovery, common troubleshooting.

**Recommended validation:**
- A new developer can follow the README to run the full test suite, execute the pipeline, and start the web app without asking questions.

**Expected outcome:** The project is self-documenting for operation.

---

#### 4.7 — Add Metrics Export

**Deficiency:** Observability is database-backed only (run manifest, reporters). No Prometheus metrics, no StatsD counters, no distributed tracing. Useful for development but not for production monitoring.

**Why Phase 4:** Production operations require real-time metrics and alerting, not just database queries.

**Recommended changes:**
- Add Prometheus client counters for pipeline runs (by pipeline name and status).
- Add Prometheus histograms for pipeline duration.
- Add a `/metrics` endpoint for web app request metrics.
- Document how to integrate with Grafana or similar dashboarding tools.

**Recommended validation:**
- Verify that `/metrics` endpoint returns Prometheus-formatted output.
- Verify that pipeline runs increment the counter.

**Expected outcome:** Application is observable via standard monitoring infrastructure.

---

## 4. Detailed Findings Table

| # | Title | Area | Severity | Evidence | Why It Matters | Recommended Change | Recommended Validation |
|---|-------|------|----------|----------|---------------|-------------------|----------------------|
| 1 | XSS via innerHTML | Implementation | High | `templates/landing.html:55`, `templates/occupation.html:171,189,208,230` | Unescaped API data executes as HTML/JS in user's browser | Use `textContent` or DOM methods; centralize `escapeHtml()` | Test that HTML characters in API responses render as text |
| 2 | SQL injection via f-string table names | Implementation | High | `validate/framework.py:39,59`, `load/onet.py:69,119`, `web/api/health.py:25,159` | Identifier injection if table names ever come from user input | Parameterize or allowlist-validate all dynamic identifiers | Test injection with crafted table names |
| 3 | No CORS middleware | Deployment | High | `web/app.py` — no CORSMiddleware | Any website can call the API, enabling data exfiltration or abuse | Add CORSMiddleware with explicit allowed origins | Test that cross-origin requests are rejected |
| 4 | No CSP header | Deployment | Medium | `web/templates/base.html` — no CSP meta tag or middleware | Increases XSS attack surface; inline scripts run unrestricted | Add CSP header; move inline scripts to external files | Test that inline script injection is blocked |
| 5 | No CLI entrypoints | Design | High | `pyproject.toml` — no `[project.scripts]` section | Project cannot be run from command line without Python REPL | Add console_scripts for web and pipeline | Verify `jobclass-web --help` works after install |
| 6 | Config path duplication | Design | Low | `config/database.py:7-8` vs `config/settings.py` | Two sources of truth for default paths | Import paths from settings.py | Verify env var override works in both layers |
| 7 | Parser utility duplication | Implementation | Medium | `parse/oews.py:10`, `parse/onet.py:52`, `parse/projections.py:34` | Inconsistent suppression handling across sources | Create `parse/common.py` with shared utilities | Existing parser tests pass unchanged |
| 8 | No input validation on API | Implementation | Medium | `web/api/occupations.py:13`, `web/api/wages.py:15` | Oversized queries, invalid parameters produce confusing responses | Add length limits, enum validation, format checks | Test 400 responses for invalid input |
| 9 | Thread-unsafe connection init | Implementation | Low | `web/database.py:21-28` — no lock on global _conn | TOCTOU race under concurrent requests | Add threading.Lock() | Concurrent access test |
| 10 | Broad exception swallowing | Implementation | Low | `extract/orchestrator.py:103`, `web/database.py:38`, `load/oews.py:62` | Silent failures hide bugs | Catch specific types; add logging | Verify exceptions are logged |
| 11 | Search race condition | Implementation | Medium | `templates/search.html:31-51` | Stale results displayed after rapid typing | Add AbortController or request counter | Manual rapid-typing test |
| 12 | Vague test assertions | Testing | Medium | 31 instances of `assert > 0` across test suite | Tests pass with wrong data loaded | Replace with exact expected counts | Break a fixture; verify test fails |
| 13 | No negative tests | Testing | High | 4 exception path tests in 376-test suite | Error handling code is untested | Add invalid input, empty result, failure tests | Each new test fails when validation removed |
| 14 | Deep fixture chains | Testing | Medium | `conftest.py:72-178` — 5-level dependency chain | Slow suite; cascading failures | Create independent per-source fixtures | SOC tests run without OEWS/O\*NET |
| 15 | No CI/CD | Deployment | High | No `.github/workflows/`, Jenkinsfile, or CI config | No automated quality enforcement | Create GitHub Actions workflow | Push failing test; verify CI rejects |
| 16 | No Dockerfile | Deployment | High | No Dockerfile or docker-compose.yml | Cannot deploy to containers | Create multi-stage Dockerfile | `docker build .` and `docker-compose up` work |
| 17 | No dependency lock file | Deployment | Medium | No requirements.lock or poetry.lock | Non-reproducible builds | Generate lock file with pip-compile | Install from lock file; run tests |
| 18 | No API pagination | Design | Medium | `web/api/occupations.py:20-29`, `web/api/wages.py:28-41` | Unbounded result sets; not scalable | Add limit/offset parameters | Test exact result counts with limit |
| 19 | Missing aria-live regions | Implementation | Low | `templates/occupation.html`, `templates/wages_comparison.html` | Screen readers don't announce dynamic content | Add aria-live="polite" and aria-busy | Screen reader verification |
| 20 | No fetch timeouts | Implementation | Low | All templates with fetch calls | Browser waits indefinitely on hung server | Add AbortController with 10s timeout | Test timeout triggers error UI |
| 21 | No static cache-busting | Deployment | Low | `templates/base.html` — hardcoded asset URLs | Stale CSS/JS after deployments | Add version query parameter | Verify cache invalidation |
| 22 | Weak health endpoint | Deployment | Low | `web/api/health.py` — no connectivity or migration check | Cannot distinguish "reachable" from "ready" | Add SELECT 1 and migration checks | Test 503 on missing db |
| 23 | No operational documentation | Methodology | Medium | README.md — no run/deploy/operate instructions | Project cannot be operated by non-authors | Add Quick Start, Deployment, Operations sections | New developer walkthrough |
| 24 | No metrics export | Deployment | Low | No Prometheus, StatsD, or APM integration | No production monitoring capability | Add prometheus_client counters and /metrics endpoint | Verify /metrics returns valid output |
| 25 | Hardcoded magic numbers | Implementation | Low | `validate/framework.py:249,259,373` — drift thresholds 20.0%, 15.0% | Undocumented thresholds; inconsistent values | Move to config or named constants with documentation | N/A — documentation improvement |
| 26 | Missing API versioning | Design | Low | All endpoints under `/api/` with no version prefix | Breaking changes affect all consumers simultaneously | Consider `/api/v1/` prefix | N/A — forward-looking |

---

## 5. Missing Things That Should Exist

| Artifact | Why It Should Exist | Priority |
|----------|-------------------|----------|
| `Dockerfile` | Required for container deployment | High |
| `.github/workflows/ci.yml` | Automated testing and linting on every push | High |
| CLI entrypoints (`console_scripts`) | Running the project from the command line | High |
| `requirements.lock` | Reproducible dependency resolution | Medium |
| `docker-compose.yml` | Local development with production-like setup | Medium |
| `parse/common.py` | Shared suppression markers and numeric parsing | Medium |
| Pydantic response models for API endpoints | Typed API contracts | Medium |
| `CONTRIBUTING.md` or developer setup guide | Onboarding for new contributors | Low |
| `/metrics` endpoint | Prometheus-compatible monitoring | Low |
| API versioning (`/api/v1/`) | Forward compatibility for breaking changes | Low |
| `.env.example` | Document required/optional environment variables | Low |
| `scripts/` directory with helper scripts | Common operations (setup, download, run) | Low |

---

## 6. Highest-Risk Areas

1. **XSS in templates** — The `innerHTML` pattern with unescaped API data is the only finding that could cause direct user harm. The attack surface is limited (data comes from federal sources, not user input to the warehouse), but the pattern is unsafe and a reviewer would reject it.

2. **Web API without input validation** — Any input (search queries, parameters) passes directly to SQL queries. While DuckDB parameterization prevents SQL injection for values, the lack of length limits and format validation means the API can be abused (e.g., 10 MB search query causing memory pressure).

3. **Test suite proves non-emptiness, not correctness** — The 31 `> 0` assertions mean the test suite would still pass if the pipeline loaded the wrong data, the wrong number of rows, or the wrong version. A data quality regression could go undetected.

4. **No CI/CD enforcement** — Ruff is configured but not enforced. Tests exist but aren't run automatically. A developer could merge code that breaks tests or violates lint rules without any automated check.

5. **Pipeline orchestration has no CLI** — The pipeline can only be run by writing Python code. This means production execution depends on scripts or notebooks that are not in the repository. If those scripts are lost, the pipeline cannot be run.

---

## 7. Recommended Next Actions

A developer or coding agent should execute these in order:

1. **Fix XSS immediately.** Move `escapeHtml()` to `main.js`. Replace all `innerHTML` assignments that include API data with `textContent` or escaped DOM construction. This is a 1-2 hour fix that eliminates the highest-severity finding.

2. **Add CORS and CSP middleware to `app.py`.** Add `CORSMiddleware` with `allowed_origins=["*"]` initially (tighten later). Add a CSP middleware that sets `Content-Security-Policy: default-src 'self'`. Move inline scripts to external files to comply with CSP.

3. **Add input validation to API endpoints.** Add `max_length=100` to search, `Literal["national", "state"]` to geo_type, regex validation to SOC codes. Return 400 for invalid input.

4. **Parameterize SQL identifiers.** Change f-string table names in `validate/framework.py` and `web/api/health.py` to use parameterized queries or allowlist validation.

5. **Add CLI entrypoints.** Create `src/jobclass/cli.py` and add `[project.scripts]` to `pyproject.toml`. This unblocks CI/CD, Dockerfile, and operational documentation.

6. **Create CI/CD workflow.** Create `.github/workflows/ci.yml` with ruff + pytest. This prevents future regressions.

7. **Replace vague test assertions.** Go through the 31 `> 0` assertions and replace with exact expected counts. This is tedious but high-value for trust.

8. **Add negative tests.** Create `TestInvalidInput` classes in web test modules. Test invalid SOC codes, empty queries, bad parameters.

9. **Create Dockerfile.** Multi-stage build: install deps, copy source, expose port, run uvicorn.

10. **Consolidate parser utilities.** Create `parse/common.py` with shared suppression markers and numeric parsing.
