# Website Test Plan — Release 1

This document defines all tests for the JobClass reporting website, aligned phase-by-phase with the [Phased Website Release Plan](phased_website_release_plan.md).

---

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

---

## Test Types

| Code | Type | Purpose |
|------|------|---------|
| UNIT | Unit Test | Verify a single function, endpoint, or component in isolation |
| API | API Test | Verify endpoint response structure, status codes, and data correctness |
| RENDER | Render Test | Verify page or component renders correct content given known data |
| E2E | End-to-End Test | Verify full user flow across multiple pages and API calls |
| A11Y | Accessibility Test | Verify WCAG compliance, keyboard navigation, semantic HTML |
| PERF | Performance Test | Verify response times, page load targets, query efficiency |
| VISUAL | Visual Test | Verify layout, responsive behavior, and visual consistency |
| CONTRACT | Contract Test | Verify API response schema stability across changes |
| ERROR | Error Handling Test | Verify graceful behavior under error conditions |

**Columns**: Status, Test ID, Type, Description, Pass Criteria, Traces To (requirement), Validates Task, Started, Completed

---

## Phase W1 Tests: Project Setup & API Foundation

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT1-01 | UNIT | Database connection module reads from existing warehouse | Connection opens successfully; query against dim_occupation returns rows | WAR-1 | W1-04 | | |
| `[ ]` | WT1-02 | API | `/api/health` returns 200 with warehouse version and table row counts | Response JSON contains `status`, `warehouse_version`, `table_counts` object with non-zero values | WAR-5 | W1-06 | | |
| `[ ]` | WT1-03 | API | `/api/metadata` returns source versions and release IDs for all loaded datasets | Response includes `soc_version`, `oews_release_id`, `onet_version`, `last_load_timestamp` | WAR-5, WFR-11 | W1-07 | | |
| `[ ]` | WT1-04 | RENDER | Base layout renders header, navigation, and footer | HTML response contains `<header>`, `<nav>`, `<footer>` elements with expected content | WNF-1, WNF-3 | W1-08 | | |
| `[ ]` | WT1-05 | ERROR | API returns structured error JSON for invalid routes | 404 response has `error` and `message` fields; no stack trace exposed | WNF-6 | W1-05 | | |
| `[ ]` | WT1-06 | CONTRACT | Health endpoint schema: `status` (string), `warehouse_version` (string), `table_counts` (object) | Schema matches expected structure; no extra or missing fields | WAR-2, WAR-5 | W1-06 | | |

---

## Phase W2 Tests: Occupation Search & Hierarchy

### Search Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT2-01 | API | Search by keyword "software" returns matching occupations | Response includes 15-1252 "Software Developers"; all results contain "software" in title or code | WFR-1 | W2-01 | | |
| `[ ]` | WT2-02 | API | Search by SOC code "15-1252" returns exact match | Response includes exactly one result with soc_code "15-1252" | WFR-1 | W2-01 | | |
| `[ ]` | WT2-03 | API | Empty search query returns empty results or all occupations | Response is valid JSON with empty results array or full listing; no error | WFR-1 | W2-01 | | |
| `[ ]` | WT2-04 | CONTRACT | Search response schema: array of `{soc_code, occupation_title, occupation_level}` | Each result has required fields; soc_code is text; occupation_level is integer | WAR-2 | W2-01 | | |
| `[ ]` | WT2-05 | RENDER | Search page renders search input and results list | Page contains `<input>` for search, results display as list items with SOC code and title | WFR-1, WNF-3 | W2-04 | | |

### Hierarchy Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT2-06 | API | Hierarchy endpoint returns tree with major → minor → broad → detailed levels | Response contains nested structure; major groups have children; leaf nodes are detailed occupations | WFR-3 | W2-02 | | |
| `[ ]` | WT2-07 | API | Hierarchy includes Computer and Mathematical (15-0000) major group | Response contains node with soc_code "15-0000" having children | WFR-3 | W2-02 | | |
| `[ ]` | WT2-08 | RENDER | Hierarchy browser renders expandable tree | Page contains tree structure with expand/collapse controls; clicking expands children | WFR-3, WNF-3 | W2-05 | | |

### Profile Page Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT2-09 | API | Profile endpoint for 15-1252 returns complete occupation data | Response includes soc_code, title, definition, hierarchy fields, soc_version | WFR-2 | W2-03 | | |
| `[ ]` | WT2-10 | RENDER | Profile page for 15-1252 displays title, SOC code, hierarchy breadcrumb, definition | Page contains "Software Developers", "15-1252", breadcrumb from major group, definition text | WFR-2, WNF-5 | W2-06 | | |
| `[ ]` | WT2-11 | RENDER | Profile page shows lineage badge with SOC version | Page displays SOC version "2018" and source_release_id | WFR-11, WAR-5 | W2-08 | | |
| `[ ]` | WT2-12 | ERROR | Profile endpoint for nonexistent SOC code returns 404 | Response status 404 with meaningful error message | WNF-6 | W2-03 | | |

---

## Phase W3 Tests: Employment & Wages Display

### Wages API Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT3-01 | API | Wages endpoint for 15-1252 returns national wage data | Response includes employment_count, mean_annual_wage, median_annual_wage; values are non-null for unsuppressed data | WFR-12 | W3-01 | | |
| `[ ]` | WT3-02 | API | Wages endpoint with `geo_type=state` returns state-level data | Response includes multiple state entries; each has geo_name, mean_annual_wage | WFR-4 | W3-03 | | |
| `[ ]` | WT3-03 | API | Geographies endpoint returns available geographies with metadata | Response includes geography entries with geo_type, geo_code, geo_name | WFR-4 | W3-02 | | |
| `[ ]` | WT3-04 | CONTRACT | Wages response schema: `{employment_count, mean_annual_wage, median_annual_wage, p10–p90, source_release_id}` | All wage fields present; numeric or null (not zero for suppressed) | WAR-2, WFR-12 | W3-01 | | |
| `[ ]` | WT3-05 | API | Suppressed wage values returned as null, not zero | For occupations with BLS suppression, wage fields are null in response | WFR-12, WNF-6 | W3-07 | | |

### Wages Display Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT3-06 | RENDER | Profile page wages section shows employment count, mean and median wages | Page displays employment_count, mean_annual_wage, median_annual_wage for 15-1252 | WFR-12, WNF-5 | W3-04 | | |
| `[ ]` | WT3-07 | RENDER | Wage distribution chart renders with percentile data | Chart element present with p10, p25, median, p75, p90 data points | WFR-12, WNF-5 | W3-05 | | |
| `[ ]` | WT3-08 | RENDER | Geography comparison page renders state-level wage table | Page contains table with state names and wage values; rows match API response count | WFR-4, WNF-5 | W3-06 | | |
| `[ ]` | WT3-09 | RENDER | Suppressed wages display as "N/A" or "suppressed", not zero | For null wage values, display shows appropriate indicator text | WFR-12, WNF-6 | W3-07 | | |
| `[ ]` | WT3-10 | RENDER | Wages section includes OEWS source lineage | Page displays OEWS release ID and reference period | WFR-11, WAR-5 | W3-08 | | |

---

## Phase W4 Tests: Skills & Tasks Display

### Skills & Tasks API Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT4-01 | API | Skills endpoint for 15-1252 returns skill names with importance and level scores | Response includes array of skills; each has skill_name, scale_type, data_value; at least 1 skill returned | WFR-5 | W4-01 | | |
| `[ ]` | WT4-02 | API | Tasks endpoint for 15-1252 returns task descriptions with scores | Response includes array of tasks; each has task_description, data_value; at least 1 task returned | WFR-6 | W4-02 | | |
| `[ ]` | WT4-03 | API | Similarity endpoint for 15-1252 returns related occupations with Jaccard scores | Response includes array of similar occupations; each has soc_code, title, jaccard_similarity between 0 and 1 | WFR-7 | W4-03 | | |
| `[ ]` | WT4-04 | CONTRACT | Skills response schema: array of `{skill_name, skill_id, scale_type, data_value, source_version}` | All fields present; data_value is numeric; source_version is non-null | WAR-2, WFR-5 | W4-01 | | |
| `[ ]` | WT4-05 | CONTRACT | Tasks response schema: array of `{task_id, task_description, task_type, data_value, source_version}` | All fields present; task_description is non-empty text | WAR-2, WFR-6 | W4-02 | | |

### Skills & Tasks Display Tests

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT4-06 | RENDER | Skill profile section renders ranked skill list for 15-1252 | Page contains skill names with scores; ordered by importance or level | WFR-5, WNF-5 | W4-04 | | |
| `[ ]` | WT4-07 | RENDER | Task profile section renders task descriptions for 15-1252 | Page contains task description text; at least 1 task visible | WFR-6, WNF-5 | W4-05 | | |
| `[ ]` | WT4-08 | RENDER | Similar occupations section shows related occupations with scores | Page lists related occupations with Jaccard similarity values | WFR-7, WNF-5 | W4-06 | | |
| `[ ]` | WT4-09 | RENDER | Skill/task sections include O*NET version lineage | Page displays O*NET source_version and release ID | WFR-11, WAR-5 | W4-07 | | |
| `[ ]` | WT4-10 | RENDER | Skill exploration page renders skill-to-occupation matrix | Page contains browsable skill listing with associated occupations | WFR-5, WNF-5 | W4-08 | | |

---

## Phase W5 Tests: Trends & Projections Display

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT5-01 | API | Projections endpoint for 15-1252 returns employment outlook | Response includes projection_cycle, employment_base, employment_projected, employment_change_pct, annual_openings | WFR-8 | W5-01 | | |
| `[ ]` | WT5-02 | CONTRACT | Projections response schema: `{projection_cycle, employment_base, employment_projected, employment_change_pct, annual_openings, education_category}` | All fields present; employment values are integers or null | WAR-2, WFR-8 | W5-01 | | |
| `[ ]` | WT5-03 | RENDER | Projections section shows base and projected employment with growth rate | Page displays base employment, projected employment, and percentage change | WFR-8, WNF-5 | W5-02 | | |
| `[ ]` | WT5-04 | RENDER | Projections chart renders base vs. projected comparison | Chart element present with two data series (base and projected) | WFR-8, WNF-5 | W5-03 | | |
| `[ ]` | WT5-05 | RENDER | Education and training requirements displayed from projection data | Page shows education category (e.g., "Bachelor's degree") | WFR-8 | W5-04 | | |
| `[ ]` | WT5-06 | RENDER | Projections section includes source lineage | Page displays projection cycle and source release ID | WFR-11, WAR-5 | W5-05 | | |
| `[ ]` | WT5-07 | RENDER | Trend comparison page renders growth rate comparison across occupations | Page contains table or chart comparing multiple occupations' growth rates | WFR-8, WNF-5 | W5-06 | | |

---

## Phase W6 Tests: Landing Page & Navigation

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT6-01 | API | Stats endpoint returns key warehouse statistics | Response includes occupation_count, geography_count, latest_release, source_count; all values non-null | WFR-10 | W6-01 | | |
| `[ ]` | WT6-02 | RENDER | Landing page displays project summary and key statistics | Page contains statistics cards with occupation count, geography count; project description present | WFR-10, WNF-5 | W6-02 | | |
| `[ ]` | WT6-03 | RENDER | Landing page includes featured occupation spotlight | Page contains spotlight section with a specific occupation's summary data | WFR-10, WNF-5 | W6-03 | | |
| `[ ]` | WT6-04 | RENDER | Navigation header contains links to all major sections | Header has links to search, hierarchy, methodology; all links resolve to valid pages | WNF-3, WNF-5 | W6-04 | | |
| `[ ]` | WT6-05 | ERROR | 404 page renders helpful navigation options | 404 page contains error message and links to search and landing page | WNF-6, WNF-5 | W6-05 | | |
| `[ ]` | WT6-06 | RENDER | All pages have unique, descriptive `<title>` and meta description | Each page's title reflects content; meta description is non-empty | WNF-4 | W6-06 | | |
| `[ ]` | WT6-07 | E2E | Navigation flow: landing → search → profile → wages → back to search | Each step renders correct page; back navigation works; no broken links | WNF-3, WNF-5 | W6-04 | | |

---

## Phase W7 Tests: Methodology & Data Transparency

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT7-01 | API | Sources endpoint returns descriptions for SOC, OEWS, O*NET, Projections | Response includes 4 source entries; each has name, description, url, refresh_cadence, current_version | WFR-9 | W7-01 | | |
| `[ ]` | WT7-02 | API | Validation endpoint returns validation summary with pass/fail counts | Response includes total_checks, passed, failed; total_checks > 0 | WFR-9 | W7-02 | | |
| `[ ]` | WT7-03 | RENDER | Methodology landing page contains project purpose and architecture overview | Page contains architecture description, data flow explanation, project motivation text | WFR-9, WNF-5 | W7-03 | | |
| `[ ]` | WT7-04 | RENDER | Data sources page describes all four sources with versions and links | Page lists SOC, OEWS, O*NET, Projections; each has description, current version, source URL | WFR-9 | W7-04 | | |
| `[ ]` | WT7-05 | RENDER | Data quality page shows validation approach and current status | Page contains validation methodology text and current pass/fail summary | WFR-9, WFR-11 | W7-05 | | |
| `[ ]` | WT7-06 | RENDER | Version info page shows all source versions and refresh timestamps | Page displays SOC version, OEWS release, O*NET version, projections cycle, load timestamps | WFR-9, WAR-5 | W7-06 | | |

---

## Phase W8 Tests: Visual Polish & Responsive Design

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT8-01 | VISUAL | Consistent visual style across all pages | Color scheme, typography, and spacing match design system; no visual inconsistencies | WNF-5 | W8-01 | | |
| `[ ]` | WT8-02 | VISUAL | Responsive layout at desktop (1280px), tablet (768px), and mobile (375px) breakpoints | All critical content visible at each breakpoint; no horizontal overflow; navigation accessible | WNF-1 | W8-02 | | |
| `[ ]` | WT8-03 | A11Y | Semantic HTML structure on all pages | All pages use appropriate heading hierarchy, landmarks, and ARIA attributes | WNF-3 | W8-03 | | |
| `[ ]` | WT8-04 | A11Y | Keyboard navigation works for all interactive elements | Tab order is logical; focus indicators visible; all actions reachable by keyboard | WNF-3 | W8-03 | | |
| `[ ]` | WT8-05 | A11Y | Color contrast meets WCAG AA standards (4.5:1 for normal text, 3:1 for large text) | Automated contrast checker passes on all text/background combinations | WNF-3 | W8-03 | | |
| `[ ]` | WT8-06 | VISUAL | Charts render consistently with tooltips, legends, and responsive sizing | Charts resize without distortion; tooltips display correct values; legends present | WNF-5, WNF-2 | W8-04 | | |
| `[ ]` | WT8-07 | RENDER | Loading states display skeleton screens while data loads | Data-dependent sections show skeleton or spinner before content appears | WNF-2, WNF-6 | W8-05 | | |
| `[ ]` | WT8-08 | PERF | All API endpoints respond within 500ms for typical queries | P95 response time < 500ms across all endpoints with test dataset | WNF-2 | W8-06 | | |
| `[ ]` | WT8-09 | PERF | Page initial render completes within 2 seconds | Time to first contentful paint < 2s on simulated 4G connection | WNF-2 | W8-06 | | |

---

## Phase W9 Tests: End-to-End Integration & Deployment

| Status | Test ID | Type | Description | Pass Criteria | Traces To | Validates Task | Started | Completed |
|--------|---------|------|-------------|---------------|-----------|----------------|---------|-----------|
| `[ ]` | WT9-01 | E2E | Full end-to-end: warehouse loaded → API started → all pages render with data | All API endpoints return 200 with non-empty data; all pages render without errors | WAR-1 through WAR-6 | W9-01 | | |
| `[ ]` | WT9-02 | E2E | Software Developers (15-1252) worked example: navigate profile → wages → skills → tasks → projections → similar | All sections display correct data for 15-1252; no empty sections; lineage visible throughout | WFR-2, WFR-4 through WFR-8 | W9-02 | | |
| `[ ]` | WT9-03 | E2E | Source lineage visible on every data display section | Every wages, skills, tasks, and projections section shows source_release_id or source_version | WFR-11 | W9-03 | | |
| `[ ]` | WT9-04 | E2E | Methodology pages complete: project purpose, sources, quality, versions all present | Methodology landing, sources, quality, and version pages all render with populated content | WFR-9 | W9-04 | | |
| `[ ]` | WT9-05 | E2E | Landing page → search "managers" → select result → profile page loads | Full navigation flow completes without errors; profile page displays correct occupation | WFR-1, WFR-2 | W9-01 | | |
| `[ ]` | WT9-06 | E2E | Error recovery: invalid SOC code → 404 → navigate to search → successful search | Application recovers gracefully from error; user can navigate away | WNF-6 | W9-01 | | |
| `[ ]` | WT9-07 | PERF | Full page load profiling: all pages meet 2-second target | Lighthouse or equivalent audit shows FCP < 2s for all pages | WNF-2 | W9-09 | | |
| `[ ]` | WT9-08 | A11Y | Full accessibility audit passes WCAG AA for all pages | Automated audit (axe-core or Lighthouse) reports zero critical violations | WNF-3 | W9-10 | | |

---

## Test Summary

| Phase | Description | Test Count |
|-------|-------------|------------|
| W1 | Project Setup & API Foundation | 6 |
| W2 | Occupation Search & Hierarchy | 12 |
| W3 | Employment & Wages Display | 10 |
| W4 | Skills & Tasks Display | 10 |
| W5 | Trends & Projections Display | 7 |
| W6 | Landing Page & Navigation | 7 |
| W7 | Methodology & Data Transparency | 6 |
| W8 | Visual Polish & Responsive Design | 9 |
| W9 | End-to-End Integration & Deployment | 8 |
| **Total** | | **75** |

### Tests by Type

| Type | Count | Purpose |
|------|-------|---------|
| UNIT | 1 | Isolated module correctness |
| API | 13 | Endpoint response and data validation |
| CONTRACT | 6 | API schema stability |
| RENDER | 23 | Page and component content correctness |
| E2E | 8 | Full user flow verification |
| A11Y | 4 | Accessibility and WCAG compliance |
| PERF | 3 | Performance and load time verification |
| VISUAL | 4 | Layout, style, and responsive design |
| ERROR | 3 | Graceful error handling |
