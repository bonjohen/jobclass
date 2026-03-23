# Phased Website Release Plan — Release 1

This document is the work-tracking artifact for the JobClass reporting website. Each task has a status, requirement traceability, and timestamps updated as work proceeds.

The website builds on the completed data pipeline (Phases 1–11 of the pipeline release plan). It exposes the analytical warehouse through a structured web experience with occupation search, geography comparison, skill and task exploration, trend display, and methodology transparency.

Source documents: [Website Architecture](base_website_architecture.md), [Website Design](base_website_design.md)

## Requirement Traceability Key

Requirements are derived from the architecture document and organized by domain.

| Prefix | Domain | Description |
|--------|--------|-------------|
| WFR | Functional | User-facing feature or data requirement |
| WAR | Architectural | Structural, layering, or integration requirement |
| WNF | Non-Functional | Performance, accessibility, usability, or quality requirement |

### Functional Requirements

| ID | Description | Source |
|----|-------------|--------|
| WFR-1 | Occupation search: find occupations by keyword, SOC code, or hierarchy position | §5.7, §7 |
| WFR-2 | Occupation profile page: hierarchy, definition, employment, wages, skills, tasks | §5.7, §7 |
| WFR-3 | Occupation hierarchy browsing: navigate major → minor → broad → detailed levels | §5.7, §7 |
| WFR-4 | Geography comparison: state-level wage and employment comparison for an occupation | §5.7, §7 |
| WFR-5 | Skill profile display: skills with importance/level scores for an occupation | §5.7, §7 |
| WFR-6 | Task profile display: task descriptions and relevance for an occupation | §5.7, §7 |
| WFR-7 | Occupation similarity: related occupations based on shared skill/task structures | §5.7, §7 |
| WFR-8 | Trend/projections display: employment outlook, base/projected employment, growth rate | §7 |
| WFR-9 | Methodology page: data source descriptions, lineage, version info, validation summary | §5.7, §7, §8 |
| WFR-10 | Overview/landing page: project summary, key statistics, navigation entry points | §5.7 |
| WFR-11 | Source lineage visibility: every displayed value traceable to source release | §8 |
| WFR-12 | Wage distribution display: mean, median, percentile wages with chart support | §7 |

### Architectural Requirements

| ID | Description | Source |
|----|-------------|--------|
| WAR-1 | Application service layer isolates website from warehouse schema | §5.6 |
| WAR-2 | API exposes business-oriented resources, not raw warehouse tables | §5.6 |
| WAR-3 | Reporting mart layer provides query-friendly data for website endpoints | §5.5 |
| WAR-4 | Publication gating: website data only refreshes after upstream validation passes | §5.3, §8 |
| WAR-5 | Versioned data: API and website must expose source version and release context | §8 |
| WAR-6 | Separation of concerns: presentation logic does not contain business logic | §4, §11 |

### Non-Functional Requirements

| ID | Description | Source |
|----|-------------|--------|
| WNF-1 | Responsive layout: usable on desktop and tablet viewports | §5.7 |
| WNF-2 | Page load performance: initial content visible within 2 seconds on typical connection | §9 |
| WNF-3 | Accessibility: semantic HTML, keyboard navigable, sufficient color contrast | §5.7 |
| WNF-4 | SEO-friendly: meaningful page titles, meta descriptions, semantic headings | §5.7 |
| WNF-5 | Portfolio quality: visually polished, demonstrates analytical product thinking | §2, §11 |
| WNF-6 | Error handling: graceful fallback when data is unavailable or API errors occur | §5.6, §5.7 |

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

**Columns**: Status, Task ID, Description, Traces To (requirement IDs), Started, Completed

---

## Phase W1: Project Setup & API Foundation

Establish the website project structure, tech stack, and application service layer. Everything downstream depends on a working API that reads from the existing warehouse.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W1-01 | Select and document website tech stack (framework, API layer, charting library, CSS approach) | WAR-1, WAR-6 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-02 | Initialize website project structure (app directory, static assets, templates or components, config) | WAR-6 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-03 | Configure development server with hot reload, linting, and test runner | WNF-2 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-04 | Create database connection module: read-only access to existing DuckDB warehouse | WAR-1, WAR-3 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-05 | Build API foundation: router structure, request/response patterns, error handling | WAR-1, WAR-2, WNF-6 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-06 | Implement `/api/health` endpoint returning warehouse version and row counts | WAR-5 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-07 | Implement `/api/metadata` endpoint returning source versions, release IDs, last load timestamps | WAR-5, WFR-11 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-08 | Create base page layout: header, navigation, footer, content area | WNF-1, WNF-3, WNF-5 | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-09 | Set up test framework for API endpoints and page rendering | — | 2026-03-23 15:00 | 2026-03-23 16:00 |
| `[X]` | W1-10 | Configure static asset pipeline (CSS, JS bundling or serving) | WNF-2 | 2026-03-23 15:00 | 2026-03-23 16:00 |

---

## Phase W2: Occupation Search & Hierarchy

Build the occupation search, listing, and hierarchy browsing experience. This is the primary entry point for users.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W2-01 | Implement `/api/occupations/search?q=` endpoint: keyword search across SOC codes and titles | WFR-1, WAR-2 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-02 | Implement `/api/occupations/hierarchy` endpoint: return hierarchy tree (major → minor → broad → detailed) | WFR-3, WAR-2 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-03 | Implement `/api/occupations/{soc_code}` endpoint: return full occupation profile data | WFR-2, WAR-2 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-04 | Build occupation search page: search box with live filtering, results list with SOC code and title | WFR-1, WNF-3 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-05 | Build occupation hierarchy browser: expandable/collapsible tree navigation | WFR-3, WNF-3 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-06 | Build occupation profile page shell: header with title, SOC code, hierarchy breadcrumb, definition | WFR-2, WNF-5 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-07 | Display hierarchy context on profile page: parent groups, sibling occupations, child specializations | WFR-2, WFR-3 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-08 | Add source lineage badge to profile page: SOC version, source release ID | WFR-11, WAR-5 | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-09 | Write search endpoint tests: keyword matching, empty query, SOC code lookup | — | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-10 | Write hierarchy endpoint tests: tree structure, parent-child relationships, level counts | — | 2026-03-23 16:30 | 2026-03-23 17:00 |
| `[X]` | W2-11 | Write profile page rendering tests: correct data displayed for known SOC code | — | 2026-03-23 16:30 | 2026-03-23 17:00 |

---

## Phase W3: Employment & Wages Display

Add employment counts and wage distribution data to occupation profiles, with geography breakdown.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W3-01 | Implement `/api/occupations/{soc_code}/wages` endpoint: national and state-level wage data | WFR-4, WFR-12, WAR-2 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-02 | Implement `/api/geographies` endpoint: list available geographies with metadata | WFR-4, WAR-2 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-03 | Implement `/api/occupations/{soc_code}/wages?geo_type=state` endpoint: state comparison data | WFR-4, WAR-2 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-04 | Build wages summary section on profile page: employment count, mean/median wages, wage percentiles | WFR-12, WNF-5 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-05 | Build wage distribution chart: bar or box chart showing p10/p25/median/p75/p90 | WFR-12, WNF-5 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-06 | Build geography comparison page: table and map/chart of state-level wages for an occupation | WFR-4, WNF-5 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-07 | Handle BLS suppression display: show "N/A" or "suppressed" for null wage values, never zero | WFR-12, WNF-6 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-08 | Add source lineage to wages section: OEWS release ID, reference period | WFR-11, WAR-5 | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-09 | Write wages endpoint tests: correct values for known occupation, suppression handling | — | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-10 | Write geography comparison tests: state count, no fan-out, null handling | — | 2026-03-23 17:15 | 2026-03-23 17:45 |
| `[X]` | W3-11 | Write chart rendering tests: data-to-visual mapping correctness | — | 2026-03-23 17:15 | 2026-03-23 17:45 |

---

## Phase W4: Skills & Tasks Display

Add O*NET skill and task profile data to occupation pages with semantic exploration.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W4-01 | Implement `/api/occupations/{soc_code}/skills` endpoint: skills with importance/level scores | WFR-5, WAR-2 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-02 | Implement `/api/occupations/{soc_code}/tasks` endpoint: task descriptions with scores | WFR-6, WAR-2 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-03 | Implement `/api/occupations/{soc_code}/similar` endpoint: similar occupations with similarity scores | WFR-7, WAR-2 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-04 | Build skill profile section on occupation page: ranked list or chart of skills by importance | WFR-5, WNF-5 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-05 | Build task profile section on occupation page: task descriptions with relevance indicators | WFR-6, WNF-5 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-06 | Build similar occupations section: list of related occupations with Jaccard similarity scores | WFR-7, WNF-5 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-07 | Add O*NET version and lineage to skill/task sections | WFR-11, WAR-5 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-08 | Build standalone skill exploration page: browse skills across occupations | WFR-5, WNF-5 | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-09 | Write skills endpoint tests: correct skill names and scores for known occupation | — | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-10 | Write tasks endpoint tests: task descriptions present, score values valid | — | 2026-03-23 18:00 | 2026-03-23 18:30 |
| `[X]` | W4-11 | Write similarity endpoint tests: non-trivial results, scores between 0 and 1 | — | 2026-03-23 18:00 | 2026-03-23 18:30 |

---

## Phase W5: Trends & Projections Display

Add employment projections and trend data to the occupation experience.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W5-01 | Implement `/api/occupations/{soc_code}/projections` endpoint: employment outlook data | WFR-8, WAR-2 | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-02 | Build projections section on profile page: base/projected employment, growth rate, annual openings | WFR-8, WNF-5 | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-03 | Build projections chart: visual comparison of base vs. projected employment | WFR-8, WNF-5 | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-04 | Display education and training requirements from projection data | WFR-8 | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-05 | Add lineage to projections section: projection cycle, source release ID | WFR-11, WAR-5 | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-06 | Build standalone trend comparison page: compare growth rates across occupations | WFR-8, WNF-5 | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-07 | Write projections endpoint tests: correct values for known occupation | — | 2026-03-23 18:45 | 2026-03-23 19:00 |
| `[X]` | W5-08 | Write trend chart rendering tests: data-to-visual correctness | — | 2026-03-23 18:45 | 2026-03-23 19:00 |

---

## Phase W6: Landing Page & Navigation

Build the overview landing page and finalize navigation across all sections.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W6-01 | Implement `/api/stats` endpoint: key warehouse statistics (occupation count, geography count, latest release) | WFR-10, WAR-2 | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-02 | Build landing page: project summary, key statistics cards, navigation entry points | WFR-10, WNF-5 | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-03 | Add featured occupation spotlight to landing page (e.g., Software Developers) | WFR-10, WNF-5 | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-04 | Finalize site navigation: header links, breadcrumbs, back-to-search patterns | WNF-3, WNF-5 | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-05 | Implement 404 and error pages with helpful navigation | WNF-6, WNF-5 | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-06 | Add page titles and meta descriptions for all pages | WNF-4 | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-07 | Write landing page tests: statistics present, navigation functional | — | 2026-03-23 19:15 | 2026-03-23 19:45 |
| `[X]` | W6-08 | Write navigation integration tests: all major paths reachable | — | 2026-03-23 19:15 | 2026-03-23 19:45 |

---

## Phase W7: Methodology & Data Transparency

Build methodology pages that explain data sources, lineage, validation, and project intent. This is critical for portfolio value.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W7-01 | Implement `/api/methodology/sources` endpoint: data source descriptions, URLs, refresh cadences | WFR-9, WAR-2 | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-02 | Implement `/api/methodology/validation` endpoint: validation summary, pass/fail counts | WFR-9, WAR-2 | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-03 | Build methodology landing page: project purpose, architecture overview, data flow diagram | WFR-9, WNF-5 | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-04 | Build data sources page: SOC, OEWS, O*NET, Projections — descriptions, versions, links | WFR-9 | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-05 | Build data quality page: validation approach, current validation status, lineage explanation | WFR-9, WFR-11 | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-06 | Build version and release info page: all source versions, last refresh timestamps | WFR-9, WAR-5 | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-07 | Write methodology endpoint tests: source descriptions complete, versions present | — | 2026-03-23 20:00 | 2026-03-23 20:30 |
| `[X]` | W7-08 | Write methodology page rendering tests: all sections present and populated | — | 2026-03-23 20:00 | 2026-03-23 20:30 |

---

## Phase W8: Visual Polish & Responsive Design

Finalize visual design, responsive behavior, accessibility, and portfolio-quality presentation.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[X]` | W8-01 | Implement consistent color scheme, typography, and spacing across all pages | WNF-5 | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-02 | Ensure responsive layout: test and fix all pages at desktop, tablet, and mobile breakpoints | WNF-1 | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-03 | Verify accessibility: semantic HTML, ARIA labels, keyboard navigation, focus management | WNF-3 | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-04 | Optimize chart rendering: consistent styling, tooltips, legends, responsive sizing | WNF-5, WNF-2 | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-05 | Add loading states and skeleton screens for data-dependent content | WNF-2, WNF-6 | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-06 | Optimize API query performance: verify sub-second response times for all endpoints | WNF-2, WAR-1 | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-07 | Write responsive layout tests: critical content visible at all breakpoints | — | 2026-03-23 20:45 | 2026-03-23 21:15 |
| `[X]` | W8-08 | Write accessibility audit: automated checks for WCAG compliance | — | 2026-03-23 20:45 | 2026-03-23 21:15 |

---

## Phase W9: End-to-End Integration & Deployment

Final verification, end-to-end testing, and deployment preparation.

| Status | Task ID | Description | Traces To | Started | Completed |
|--------|---------|-------------|-----------|---------|-----------|
| `[ ]` | W9-01 | Run full end-to-end test: load warehouse → start API → navigate all pages → verify data displayed | WAR-1 through WAR-6 | | |
| `[ ]` | W9-02 | Verify Software Developers (15-1252) worked example: profile, wages, skills, tasks, projections, similar | WFR-2, WFR-4, WFR-5, WFR-6, WFR-7, WFR-8 | | |
| `[ ]` | W9-03 | Verify all source lineage visible on every data display | WFR-11 | | |
| `[ ]` | W9-04 | Verify methodology pages are complete and accurate | WFR-9 | | |
| `[ ]` | W9-05 | Cross-browser testing: verify functionality in Chrome, Firefox, Safari | WNF-1, WNF-5 | | |
| `[ ]` | W9-06 | Configure production deployment (static build, server config, environment variables) | — | | |
| `[ ]` | W9-07 | Create deployment documentation | — | | |
| `[ ]` | W9-08 | Write end-to-end smoke tests: critical paths through the application | — | | |
| `[ ]` | W9-09 | Performance profiling: verify page load targets, identify and fix bottlenecks | WNF-2 | | |
| `[ ]` | W9-10 | Final review: confirm all website requirements are met, portfolio quality verified | WNF-5 | | |

---

## Phase Summary

| Phase | Description | Task Count | Dependencies |
|-------|-------------|------------|--------------|
| W1 | Project Setup & API Foundation | 10 | Pipeline Phases 1–11 |
| W2 | Occupation Search & Hierarchy | 11 | W1 |
| W3 | Employment & Wages Display | 11 | W1, W2 |
| W4 | Skills & Tasks Display | 11 | W1, W2 |
| W5 | Trends & Projections Display | 8 | W1, W2 |
| W6 | Landing Page & Navigation | 8 | W2, W3, W4, W5 |
| W7 | Methodology & Data Transparency | 8 | W1, W6 |
| W8 | Visual Polish & Responsive Design | 8 | W2 through W7 |
| W9 | End-to-End Integration & Deployment | 10 | All prior phases |
| **Total** | | **85** | |

---

## Dependency Graph

```
Pipeline Phases 1–11 (complete)
          │
          ▼
    Phase W1 ──┬──► Phase W2 ──┬──► Phase W3 ──┐
               │               │               │
               │               ├──► Phase W4 ──┤
               │               │               │
               │               ├──► Phase W5 ──┤
               │               │               │
               │               ▼               ▼
               │          Phase W6 ◄───────────┘
               │               │
               ▼               ▼
          Phase W7 ◄──── Phase W6
               │
               ▼
          Phase W8 (depends on W2–W7)
               │
               ▼
          Phase W9 (depends on all prior)
```
