# Phased Release Plan — Pipeline Mockup Gallery

Remediation plan for the 15 backlog items identified during visual review of the Pipeline Explorer mockup gallery (`docs/mockups/`). Organizes fixes into 5 phases based on dependency order and file grouping.

Source of truth for issues: `docs/mockups/backlog.md` (BL-01 through BL-15).

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |

## How To Use This Document

Use this document as a work queue, managing the Status of each item according to the status key. Started and Completed columns are datetimes in PST.
Always assign a task a status of [>] before beginning work. Mark work as complete [X] when it is complete.

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase MK-P1: Crosswalk Promotion & Hover Consistency

Foundation phase. The crosswalk-is-required decision cascades across 4 mockups and the live code. Hover consistency is a global CSS fix applied to all 7 drill-in mockups. No dependencies on other phases.

**Files modified**: `pipeline_graph_data.js`, `01_data_sources.html`, `02_raw_landing.html`, `03_stage_parse.html`, `05_core_warehouse.html`, `06_time_series.html`, `07_marts_web.html`

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | MK-P1-01 | **BL-05 code fix**: In `src/jobclass/web/static/js/pipeline_graph_data.js`, change 5 SOC Crosswalk edges from `EDGE_TYPES.OPTIONAL` to `EDGE_TYPES.REQUIRED` (src_crosswalk→proc_download_mgr, proc_download_mgr→store_raw_xwalk, store_raw_xwalk→proc_parse_xwalk, proc_parse_xwalk→gate_schema_drift, gate_soc_alignment→store_crosswalk) | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P1-02 | **BL-05 mockup**: In `01_data_sources.html`, change SOC Crosswalk hexagon from gray dashed to blue solid (#3b82f6), change arrow to required styling | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P1-03 | **BL-07**: In `02_raw_landing.html`, change Raw Crosswalk Files cylinder from gray dashed to solid #e91e63 (matching other raw nodes) | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P1-04 | **BL-08**: In `03_stage_parse.html`, change Crosswalk Parser node from gray dashed to solid #4caf50 (matching other parser nodes) | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P1-05 | **BL-10**: In `05_core_warehouse.html`, change SOC Crosswalk Mappings node from dashed to solid #1976d2, fix footer text removing "(optional)" | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P1-06 | **BL-15**: Add `.node` CSS class and hover rule (`.node { cursor: pointer; transition: filter 0.2s; } .node:hover { filter: brightness(1.15); }`) to all drill-in mockups 01–07. Apply class to every `<g>` element wrapping a node (hexagons, cylinders, rects, diamonds, pills). | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P1-07 | Verify: open each modified mockup in browser, confirm crosswalk nodes render as required (solid borders, correct colors), confirm hover brightness effect on all nodes | 2026-03-26 10:14 | 2026-03-26 10:14 |

---

## Phase MK-P2: Individual Diagram Fixes

Targeted fixes for label positioning, node overlap, obscured elements, and arrow accuracy. Each task modifies a single file. Can be parallelized.

**Files modified**: `01_data_sources.html`, `02_raw_landing.html`, `04_validation_gates.html`, `05_core_warehouse.html`

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | MK-P2-01 | **BL-02**: In `01_data_sources.html`, move "BLS sources only" condition label from (510, 400) to (~510, 360) or offset right so it doesn't overlap with Browser Header Workaround node at translate(470, 430) | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P2-02 | **BL-06**: In `02_raw_landing.html`, fix overlapping cylinder spacing. Change y-offsets from 82/157/232/307/382/432 to uniform 80px gaps: 82/162/242/322/402/482. Increase SVG height to 620. Realign ghost arrows on both sides to match new node centers. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P2-03 | **BL-09**: In `04_validation_gates.html`, fix 4 issues: (1) remove duplicate Schema Drift `<g>` element, (2) reroute blocked-path Bezier so it passes below Referential Integrity diamond (adjust control point to ~Q 300 280), (3) move "drift blocks publication" label down to ~y=270, (4) verify SOC Alignment output edge and "SOC loads first" label don't clip bottom diamonds | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P2-04 | **BL-11**: In `05_core_warehouse.html`, fix arrow accuracy: verify dim_geography→fact_wages FK edge is visible, add ghost arrow for "CPI→Time-Series deflation" from CPI Dimensions, add ghost arrow for "Crosswalk→comparable history" from SOC Crosswalk. Verify all internal edges match GRAPH_EDGES data for nodes in the core lane. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P2-05 | Verify: open each modified mockup, confirm no overlapping elements, all labels readable, all arrows connect correct nodes | 2026-03-26 10:14 | 2026-03-26 10:14 |

---

## Phase MK-P3: Summary Topology & Core/Time-Series Merge

Structural changes: merge Time-Series into Core Warehouse at both summary and drill-in levels. This is the largest change — the Core Warehouse drill-in grows from 8 to 14 nodes, and the summary topology drops from 8 to 7 blocks.

**Files modified**: `00_summary_topology.html`, `05_core_warehouse.html`, `06_time_series.html`

**Dependencies**: MK-P2-04 (BL-11 arrow fixes) should complete before BL-12 rewrites the same file.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | MK-P3-01 | **BL-03**: In `00_summary_topology.html`, establish uniform spacing: 160px block width, 40px gaps, 200px center-to-center on main spine. Reposition all blocks to an even grid. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-02 | **BL-04**: In `00_summary_topology.html`, remove Time-Series as a standalone block. Show it as a sub-block attached below Core Warehouse (smaller box, #9c27b0 accent, loop arrow). Update arrows so Core→Marts flow passes through the time-series annotation. Summary goes from 8 to 7 top-level blocks. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-03 | **BL-12 layout**: In `05_core_warehouse.html`, expand SVG to ~920x920. Keep existing 8 core nodes in upper section. Add section divider line with "TIME-SERIES ENRICHMENT" label. Add #9c27b0-accented lower section lane background. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-04 | **BL-12 nodes**: Add 6 time-series process nodes to lower section: Metric Catalog Builder, Time Period Builder, Multi-Vintage OEWS Loading (primary, thicker border), CPI Deflation, Derived Series Computation (#3b82f6), Comparable History Logic (dashed, conditional). | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-05 | **BL-12 internal edges**: Add 6 time-series internal edges: Metrics→Periods (solid), Periods→Observations (solid), Observations→CPI Deflation (amber dashed, "nominal→real"), Observations→Derived (blue dotted), CPI Deflation→Derived (blue dotted), Comparable→Observations (amber dashed, "comparable history"). | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-06 | **BL-12 cross-section edges**: Add 4 labeled paths from core nodes to time-series nodes: fact_wages→OEWS Loading ("employment + wages"), dim_occupation→Metric Catalog ("occupation keys"), CPI Dimensions→CPI Deflation ("CPI indices"), SOC Crosswalk→Comparable History ("crosswalk mappings"). | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-07 | **BL-12 ghost arrows**: Remove old "to Time-Series →" ghost arrows from upper section. Add "to Marts →" ghost arrow from Derived Series. Update subtitle to "14 nodes · 2 sections". Update footer counts. Add Process and Derived legend entries. Add arrow-derived marker definition. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P3-08 | **BL-12 cleanup**: Convert `06_time_series.html` to a redirect/note pointing to the merged Core Warehouse diagram, or remove it. | 2026-03-26 12:30 | 2026-03-26 12:35 |
| `[X]` | MK-P3-09 | Verify: open summary topology (7 blocks, uniform spacing, Time-Series sub-block), open core warehouse (14 nodes in 2 sections, all edges visible, legend complete) | 2026-03-26 12:35 | 2026-03-26 12:35 |

---

## Phase MK-P4: Marts & Web Rewrite

Major rewrite of the Marts & Web diagram to split the single "API & Web Pages" lane into a 3-column layout (Marts → APIs → Pages) and fix all arrow issues.

**Files modified**: `07_marts_web.html`

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | MK-P4-01 | **BL-13 layout**: Expand SVG to ~1200x780. Create 3-column layout with lane backgrounds: Analyst Marts (#00bcd4, left), API Endpoints (#ff9800, middle), Web Pages (#ffd744, right). | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-02 | **BL-13 API nodes**: Add 7 API endpoint nodes in middle column (small rounded rects, #ff9800 accent): Search API, Hierarchy API, Occupation API, Wages API, Trends API, CPI API, Health API. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-03 | **BL-13 web nodes**: Place 12 web page nodes in right column (pills, #ffd744 accent): Search Page, Hierarchy Browser, Occupation Profile, Wage Comparison, Trend Explorer, Occupation Compare, Geography Compare, Ranked Movers, CPI Explorer, Methodology, Lessons, Pipeline Explorer. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-04 | **BL-14 mart→API edges**: Draw required arrows from each mart to its API endpoint(s): occupation_summary→Search/Hierarchy/Occupation APIs, wages_geo→Wages API, skill_profile→Occupation API, trend/geo_gap/rank→Trends API, similarity→Occupation API (optional/dashed). | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-05 | **BL-14 API→page edges**: Draw required arrows from API endpoints to web pages: Search API→Search Page, Hierarchy API→Hierarchy Browser, Occupation API→Occupation Profile, Wages API→Wage Comparison, Trends API→Trend Explorer/Occ Compare/Geo Compare/Ranked Movers, CPI API→CPI Explorer. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-06 | **BL-14 special nodes**: Mark Methodology and Lessons as "content-only" with ghost incoming arrows. Keep Pipeline Explorer as self-referential with dashed border. Add explicit "dim_cpi (Core)" incoming arrow to CPI API. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-07 | **BL-14 deploy edges**: Replace converging ghost arrows with a collector bar at right edge — vertical bar at x=right, one arrow from bar to "build_static.py" label. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-08 | Update subtitle and footer: "7 marts · 7 APIs · 12 web pages · 3-column data flow: Marts → APIs → Pages". Update legend with Mart, API Endpoint, Web Page entry types. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P4-09 | Verify: open marts diagram, confirm 3-column layout, all edge chains traceable, no overlapping arrows, collector bar clean | 2026-03-26 10:14 | 2026-03-26 10:14 |

---

## Phase MK-P5: New Content & Gallery Updates

Create the missing Build & Deploy mockup and update the navigation gallery to reflect all structural changes (Time-Series merge, new mockup, updated node counts).

**Files modified**: `08_build_deploy.html` (new), `index.html`, `mockup_plan.md`, `backlog.md`

**Dependencies**: All prior phases should be complete before gallery updates.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | MK-P5-01 | **BL-01 layout**: Create `08_build_deploy.html` with 5 deployment nodes, #795548 accent, ~700x450 SVG. Lane label: "Build & Deploy — Static Site Pipeline". Include grid, hover effects, back link. | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P5-02 | **BL-01 nodes**: CLI Commands (orchestration hub, top-left), Static Site Builder, Fetch Shim Injection, Deploy to GitHub Pages, Health Check. Sequential chain: build_static→fetch_shim→deploy. Conditional edges from CLI labeled "build-static", "deploy", "status". | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P5-03 | **BL-01 ghost arrows**: Ghost incoming from "12 interface pages" and "API responses". Ghost outgoing to "gh-pages branch" and "GitHub Pages". | 2026-03-26 10:14 | 2026-03-26 10:14 |
| `[X]` | MK-P5-04 | Update `index.html` sidebar: remove standalone Time-Series entry (or redirect to Core Warehouse), update Core Warehouse badge from "8" to "14", add Build & Deploy entry (accent #795548, badge "5"), update description text and gallery subtitle. Reindex data-index attributes. | 2026-03-26 12:40 | 2026-03-26 12:40 |
| `[X]` | MK-P5-05 | Update `mockup_plan.md`: add MK-08 row for Build & Deploy mockup. | 2026-03-26 12:40 | 2026-03-26 12:45 |
| `[X]` | MK-P5-06 | Update `backlog.md`: mark all 15 items as `[X]` resolved, move them to the Resolved section. | 2026-03-26 12:40 | 2026-03-26 12:45 |
| `[X]` | MK-P5-07 | Verify: open index.html, navigate all mockups via sidebar and prev/next buttons, confirm arrow keys cycle correctly through the updated list, confirm all badges match actual node counts | 2026-03-26 12:45 | 2026-03-26 12:45 |

---

## Summary

| Phase | Tasks | Backlog Items | Key Change |
|-------|-------|---------------|------------|
| MK-P1 | 7 | BL-05, BL-07, BL-08, BL-10, BL-15 | Crosswalk required everywhere, hover consistency |
| MK-P2 | 5 | BL-02, BL-06, BL-09, BL-11 | Per-diagram label/overlap/arrow fixes |
| MK-P3 | 9 | BL-03, BL-04, BL-12 | Merge Time-Series into Core Warehouse |
| MK-P4 | 9 | BL-13, BL-14 | 3-column Marts → APIs → Pages rewrite |
| MK-P5 | 7 | BL-01 | Build & Deploy mockup + gallery updates |
| **Total** | **37** | **15** | |
