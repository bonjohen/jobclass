# Project Retrospective — JobClass

This document captures what was done during the development of the JobClass project, organized by phase. It serves as a project overview for a retrospective discussion.

## Project Timeline

All work was completed on **2026-03-23**, across 26 commits over approximately 3 hours. The project went from an empty repository to a fully functional data pipeline and web application with 484 passing tests.

## How We Worked

The project was a collaboration between a human director and an AI implementer (Claude). The human provided:

- The initial **design document** (`base_design_document.md`) — a detailed architectural specification for a four-layer data warehouse ingesting federal labor market data
- A **project detail design** (`project_detail_design.md`) — requirements framed from the perspective of downstream consumers
- Direction at each major inflection point (pipeline complete, start website, run code review)
- Review and course correction as phases were completed

Claude (the AI) handled:
- Translating design documents into **phased release plans** with task-level tracking
- Generating **test plans** aligned to each release phase
- All code implementation, test writing, and documentation
- Self-directed code review with a structured remediation plan

The workflow followed a consistent pattern: the human would provide a design specification or directive, Claude would produce a phased release plan from it, then implement each phase sequentially — writing code, running tests, and committing after each phase passed.

---

## Phase 1: Project Foundation

**Commit**: `a6f7ce1` | **Tasks**: 8

Established the repository skeleton: Python project with `pyproject.toml`, DuckDB database engine, SQL migration framework, configuration module with environment variable support, structured logging, and the pytest test harness. Every subsequent phase depended on this foundation.

**Key decision**: DuckDB as the analytical database. It provides columnar storage, SQL support, and zero-infrastructure deployment — the entire warehouse is a single file.

## Phase 2: Extraction Framework & Run Manifest

**Commit**: `0b16642` | **Tasks**: 9

Built the declarative extraction system: a YAML source manifest describing each federal data product, a `run_manifest` table for tracking pipeline execution state, download orchestration with checksums, and version detection. The manifest-driven approach meant adding a new data source required only a YAML entry and a parser, not new orchestration code.

## Phase 3: SOC Taxonomy Pipeline

**Commit**: `751d7fd` | **Tasks**: 12

The first end-to-end data pipeline. Parsed SOC hierarchy and definitions CSVs, loaded staging tables, conformed `dim_occupation` (the central dimension the entire warehouse revolves around), and built `bridge_occupation_hierarchy` for parent-child traversal. Introduced the pattern every subsequent pipeline would follow: parse → stage → dimension → bridge → validate.

**Key decision**: Occupation as the stable external key. The SOC code (e.g., `15-1252`) is the grain of nearly every table.

## Phase 4: OEWS Employment & Wages Pipeline

**Commit**: `e80c481` | **Tasks**: 13

Parsed OEWS national and state CSV files with suppression-aware numeric handling (BLS uses `*`, `**`, `#` to suppress values). Created `dim_geography`, `dim_industry`, and `fact_occupation_employment_wages`. The fact table preserves source nulls rather than imputing — a design principle that carried through the entire project.

**Challenge**: BLS files use multiple suppression markers with subtly different meanings. The parser had to recognize all of them and convert to explicit nulls.

## Phase 5: O*NET Semantic Pipeline

**Commit**: `c361060` | **Tasks**: 14

Parsed O\*NET skills, knowledge, abilities, and tasks. Created four dimension tables and four bridge tables. The "split bridges" decision (separate `bridge_occupation_skill`, `bridge_occupation_knowledge`, etc. rather than a generic EAV table) added more tables but made queries clearer and type-safer.

**Key decision**: Split semantic bridges over a generic EAV table. More tables, but each has a clear schema.

## Phase 6: Validation Framework & Failure Handling

**Commit**: `647c487` | **Tasks**: 12

Built reusable validation functions: structural (required columns, column types), grain uniqueness, referential integrity, temporal monotonicity, append-only checks, schema drift detection, row-count shift detection, and measure delta analysis. Added failure classification (`download_failure`, `schema_drift_failure`, etc.) and publication gating — the warehouse won't publish if validations fail.

## Phase 7: Observability & Run Reporting

**Commit**: `8e33ca1` | **Tasks**: 10

Added run inspection, row-count delta reporting between releases, schema drift reporters, and reconciliation summaries. This phase was about making the pipeline's behavior visible — not just "did it succeed?" but "what changed and by how much?"

## Phase 8: Orchestration

**Commit**: `2db4542` | **Tasks**: 11

Built the pipeline orchestration layer: logical pipelines (`taxonomy_refresh`, `oews_refresh`, `onet_refresh`, `projections_refresh`, `warehouse_publish`), dependency enforcement (SOC must complete before occupation conformance), publish gating, and idempotent execution (re-running the same version produces no duplicates).

## Phase 9: Analyst Marts

**Commit**: `8c3fefe` | **Tasks**: 10

Created five denormalized views for analyst consumption: `occupation_summary`, `occupation_wages_by_geography`, `occupation_skill_profile`, `occupation_task_profile`, and `occupation_similarity_seeded` (Jaccard similarity between occupations based on shared skills/knowledge/abilities). Added query validation tests against known expected values.

## Phase 10: Employment Projections

**Commit**: `d407a80` | **Tasks**: 9

Extended the pipeline with BLS Employment Projections data: a new parser, staging table, and `fact_occupation_projections` with base/projected employment, growth rates, annual openings, and education/training requirements.

## Phase 11: End-to-End Integration & Deliverables

**Commit**: `39bdaf3` | **Tasks**: 8

Full integration testing: ran the complete pipeline end-to-end, verified schema documentation, sample queries, and all deliverables from the original design document. This was the pipeline's "done" checkpoint — 243 tests passing.

---

## Website Planning

**Commit**: `a6fd4f9`

The human provided a website design document (`base_website_design.md` and `base_website_architecture.md`). Claude generated a 9-phase website release plan with 85 tasks and a 75-test plan, following the same phased approach as the pipeline.

## Phase W1: Project Setup & API Foundation

**Commit**: `3bc527b` | **Tests**: Foundation

Created the FastAPI application, health and metadata API endpoints, Jinja2 template engine with base layout, CSS stylesheet, and the web test framework (TestClient with warehouse fixture). Established the pattern: API endpoints return JSON, page routes render templates that load data via JavaScript fetch calls.

## Phase W2: Occupation Search & Hierarchy

**Commit**: `978c299` | **Tests**: 16

Built search (keyword/SOC code), hierarchy tree (full SOC taxonomy with expand/collapse), and occupation profile endpoints and pages. The profile page is the central page of the site — everything links to it.

## Phase W3: Employment & Wages Display

**Commit**: `6c3a2bd` | **Tests**: 13

Wages API with geography filtering, state-level wage comparison table, suppression handling (null values display as "N/A" instead of misleading zeros). Added `dim_geography` API for the geography selector.

## Phase W4: Skills & Tasks Display

**Commit**: `8fc5e7c` | **Tests**: 13

Skills, tasks, and similarity APIs with O\*NET source lineage. Each section on the occupation profile page shows source version for traceability. The similarity endpoint returns Jaccard-based similar occupations.

## Phase W5: Employment Projections Display

**Commit**: `2b1f998` | **Tests**: 9

Projections API returning employment outlook, growth rates, and education requirements. Integrated into the occupation profile page.

## Phase W6: Landing Page & Navigation

**Commit**: `7381fc1` | **Tests**: 14

Stats API for the landing page (occupation count, geography count, skill count), spotlight section featuring a sample occupation, and the site navigation structure.

## Phase W7: Methodology & Data Transparency

**Commit**: `434270b` | **Tests**: 14

Sources API listing all four federal data products with metadata. Validation API exposing pipeline check results on the methodology page. The goal: anyone viewing the site can verify what data is loaded and whether it passed quality checks.

## Phase W8: Visual Polish & Responsive Design

**Commit**: `c68c876` | **Tests**: 14

Responsive CSS for mobile/tablet, accessibility improvements (ARIA labels, skip-to-content link, focus management), and performance sanity checks.

## Phase W9: End-to-End Integration

**Commit**: `37dde75` | **Tests**: 376 total

E2E smoke tests verifying the full user journey: landing → search → profile → wages/skills/tasks/projections/similar. Lineage verification: every displayed value traces back to its source. Full suite: 376 tests (243 pipeline + 133 web).

---

## Code Review Remediation

After the website was complete, the human directed a code review. Claude ran a structured code review against the entire codebase, producing a findings document (`code_review_plan.md`) with 26 findings across 4 severity levels. These were organized into a 95-task phased remediation plan (`phased_code_review_release_plan.md`).

### Phase CR1: Foundation and Clarity

**Commit**: `7032048` | **Tasks**: 19 | **Tests**: 395

Security hardening: XSS prevention (centralized `escapeHtml`/`escapeAttr`, DOM methods instead of `innerHTML`), SQL injection prevention (parameterized queries, regex allowlist for dynamic identifiers), CORS middleware, CSP headers. Also: CLI entrypoints (`jobclass-pipeline`, `jobclass-web`) and configuration consolidation.

**Finding highlight**: Several templates used `innerHTML` with API response data — a classic XSS vector. Fixed by extracting all inline JavaScript to external files and using DOM methods with `textContent`.

### Phase CR2: Correctness and Maintainability

**Commit**: `288fbee` | **Tasks**: 29 | **Tests**: 407

Parser consolidation (three parsers had near-identical suppression-handling code → unified `parse/common.py`), input validation on all API endpoints (SOC code regex, geo_type allowlist, search max_length), thread-safe database connection initialization, specific exception handling (replaced `except Exception: pass` with specific catches), inline script extraction to external JS files, search race condition fix (`AbortController`), and Pydantic response models for all 15 API endpoints.

**Challenge**: Extracting inline scripts broke 5 existing XSS tests that checked for JavaScript content in HTML responses. Had to rewrite those tests to check external JS files instead.

### Phase CR3: Test and Release Confidence

**Commit**: `37314b6` | **Tasks**: 22 | **Tests**: 448

Strengthened assertions (replaced vague `assert len(x) > 0` with specific expected values), added negative tests for all invalid input paths (bad SOC codes, nonexistent occupations, empty searches), parser edge case tests, Pydantic schema validation tests for all endpoints, CI/CD pipeline (`.github/workflows/ci.yml` with Python matrix, ruff lint, pytest with coverage), multi-stage Dockerfile, docker-compose, and dependency lock files.

### Phase CR4: Operational and Reviewer Polish

**Commit**: `a15ca17` | **Tasks**: 25 | **Tests**: 484

API pagination (limit/offset/total on search and wages), accessibility (aria-live regions, aria-busy toggling, keyboard navigation for hierarchy tree, proper autocomplete attribute), fetch timeouts with `AbortController` on all JS fetch calls, error state UI for all dynamic sections, static asset cache-busting, enhanced health endpoint with `SELECT 1` connectivity check, `/api/ready` readiness probe, Prometheus metrics (`/metrics` endpoint with request counters and duration histograms), operational documentation (Quick Start, Deployment, Operations sections in README), `.env.example`, and extracted hardcoded drift thresholds to named constants.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total commits | 26 |
| Pipeline phases | 11 |
| Website phases | 9 |
| Code review phases | 4 |
| Planning commits | 2 |
| Total tests | 484 |
| Pipeline tests | 243 |
| Web tests | 241 |
| Code review tasks completed | 95 / 95 |
| Data sources integrated | 4 (SOC, OEWS, O\*NET, BLS Projections) |
| Core tables | 9 dimensions + 2 facts + 4 bridges |
| Analyst marts | 5 views |
| API endpoints | 17 (including health, ready, metrics) |
| Web pages | 6 (landing, search, hierarchy, profile, wages comparison, methodology) |

## What Went Well

- **Phased approach**: Breaking work into small, testable phases with explicit task tracking made progress visible and reduced risk. Each phase had a clear "done" criterion: tests pass, commit.
- **Design-first**: Starting with a detailed design document meant implementation was translation rather than invention. Fewer surprises, fewer rework cycles.
- **Test discipline**: Writing tests alongside code caught issues immediately. The test count grew monotonically — no phase reduced coverage.
- **Code review as a phase**: Treating the code review as a structured, phased remediation (not ad-hoc fixes) produced systematic improvements.

## What Could Be Improved

- **Fixture data management**: The web test fixtures are complex (loading 4 data sources into DuckDB per test session). As the fixture grows, test times increase. A pre-built fixture file could speed this up.
- **Frontend architecture**: The JavaScript is vanilla ES5 with `innerHTML` string building. A component framework (even lightweight like Alpine.js or htmx) would reduce the manual DOM manipulation and make the code more maintainable.
- **API versioning**: The API has no version prefix (`/api/` rather than `/api/v1/`). Adding versioning now would be a breaking change for any consumers.
- **Real integration testing**: The pipeline tests use sample fixture files, not actual BLS/O\*NET downloads. A periodic integration test against real source files would catch format changes earlier.
