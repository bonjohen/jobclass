# Phased Release Plan — Lessons Section

This document tracks the work required to add the educational "Lessons" section to the JobClass web application, following the content defined in `lessons_design.md`.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase L1: Infrastructure & Landing Page

Add the navigation link, CSS styles, route handlers, and the lessons landing page.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | L1-01 | Add "Lessons" nav link to `base.html` after "Methodology" | 2026-03-24 | 2026-03-24 |
| `[X]` | L1-02 | Add `.lessons-page`, `.lessons-section`, `.lesson-card`, and code block CSS to `main.css` | 2026-03-24 | 2026-03-24 |
| `[X]` | L1-03 | Add route handlers in `app.py` for `/lessons` and all 8 lesson sub-pages | 2026-03-24 | 2026-03-24 |
| `[X]` | L1-04 | Create `lessons.html` landing page template with card grid linking to all 8 lessons | 2026-03-24 | 2026-03-24 |
| `[X]` | L1-05 | Verify: landing page renders at `/lessons` with correct nav highlighting | 2026-03-24 | 2026-03-24 |

---

## Phase L2: Data Foundation Lessons (1–4)

Create the first four lesson pages covering federal data sources, dimensional modeling, multi-vintage data, and data quality.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | L2-01 | Create `lessons_federal_data.html` — Lesson 1: The Federal Labor Data Landscape | 2026-03-24 | 2026-03-24 |
| `[X]` | L2-02 | Create `lessons_dimensional_modeling.html` — Lesson 2: Dimensional Modeling for Labor Data | 2026-03-24 | 2026-03-24 |
| `[X]` | L2-03 | Create `lessons_multi_vintage.html` — Lesson 3: The Multi-Vintage Challenge | 2026-03-24 | 2026-03-24 |
| `[X]` | L2-04 | Create `lessons_data_quality.html` — Lesson 4: Data Quality Traps in Government Sources | 2026-03-24 | 2026-03-24 |
| `[X]` | L2-05 | Add prev/next navigation links at the bottom of each lesson page | 2026-03-24 | 2026-03-24 |
| `[X]` | L2-06 | Verify: all 4 lesson pages render correctly with code blocks, tables, and diagrams | 2026-03-24 | 2026-03-24 |

---

## Phase L3: Engineering Lessons (5–8)

Create the remaining four lesson pages covering time-series normalization, idempotent pipelines, static site generation, and testing/deployment.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | L3-01 | Create `lessons_time_series.html` — Lesson 5: Time-Series Normalization | 2026-03-24 | 2026-03-24 |
| `[X]` | L3-02 | Create `lessons_idempotent_pipelines.html` — Lesson 6: Idempotent Pipeline Design | 2026-03-24 | 2026-03-24 |
| `[X]` | L3-03 | Create `lessons_static_site.html` — Lesson 7: Static Site Generation | 2026-03-24 | 2026-03-24 |
| `[X]` | L3-04 | Create `lessons_testing_deployment.html` — Lesson 8: Testing and Deployment | 2026-03-24 | 2026-03-24 |
| `[X]` | L3-05 | Add prev/next navigation links to lessons 5–8, connecting to lessons 1–4 sequence | 2026-03-24 | 2026-03-24 |
| `[X]` | L3-06 | Verify: all 8 lesson pages render correctly end-to-end | 2026-03-24 | 2026-03-24 |

---

## Phase L4: Web Tests

Add automated tests for all lesson pages to match the existing web test patterns.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | L4-01 | Create `tests/web/test_lessons.py` with test class for landing page (status 200, has card grid, links to all 8 lessons) | 2026-03-24 | 2026-03-24 |
| `[X]` | L4-02 | Add tests for each lesson page: status 200, correct title, has lesson content sections | 2026-03-24 | 2026-03-24 |
| `[X]` | L4-03 | Add test: prev/next navigation links point to valid lesson URLs | 2026-03-24 | 2026-03-24 |
| `[X]` | L4-04 | Add test: all lesson pages include code blocks rendered correctly | 2026-03-24 | 2026-03-24 |
| `[X]` | L4-05 | Add test: nav bar "Lessons" link present on all pages | 2026-03-24 | 2026-03-24 |
| `[X]` | L4-06 | Run full test suite — all existing + new tests pass | 2026-03-24 | 2026-03-24 |

---

## Phase L5: Static Site Integration & Deployment

Update the static site generator, rebuild, and deploy.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | L5-01 | Add `/lessons` path rewriting entries to `build_static.py` `rewrite_paths()` | 2026-03-24 | 2026-03-24 |
| `[X]` | L5-02 | Add lesson HTML page generation to `build_static.py` (landing + 8 lesson pages) | 2026-03-24 | 2026-03-24 |
| `[X]` | L5-03 | Run `ruff format` and `ruff check` on all changed files | 2026-03-24 | 2026-03-24 |
| `[>]` | L5-04 | Commit all lessons work | 2026-03-24 | |
| `[ ]` | L5-05 | Push to GitHub and verify CI passes | | |
| `[X]` | L5-06 | Update `README.md` with lessons section info and updated test count | 2026-03-24 | 2026-03-24 |

---

## Phase Summary

| Phase | Description | Tasks | Status |
|-------|-------------|-------|--------|
| L1 | Infrastructure & Landing Page | 5 | Complete |
| L2 | Data Foundation Lessons (1–4) | 6 | Complete |
| L3 | Engineering Lessons (5–8) | 6 | Complete |
| L4 | Web Tests | 6 | Complete |
| L5 | Static Site Integration & Deployment | 6 | In progress |
| **Total** | | **29** | |
