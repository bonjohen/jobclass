# Phased Release Plan — Pipeline Explorer

This document tracks the work required to add the interactive Pipeline Explorer page to the JobClass web application, following the requirements in `pipeline_explorer_design.md`.

The Pipeline Explorer is a canvas-based, graph-driven visualization of the entire JobClass pipeline — from federal data sources through extraction, staging, core warehouse, marts, APIs, and web pages. It uses semantic zoom, guided educational modes, and rich detail panels to make the system explorable and teachable. No third-party libraries; consistent with the project's vanilla-JS approach.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

## How To Use This Document.

Use this document as a work queue, managing the Status of each item according to the status key. Started and Completed columns are datetimes in PST.
Always assign a task a status of [>] before beginning work. Mark work as complete [X] when it is complete. This is the central file that will show status, and tell you which items to work next. 


**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase PE0: Infrastructure & Route Setup

Add the navigation link, route, template scaffold, empty JS/CSS files, and verify the page loads.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE0-01 | Add "Pipeline" nav link to `base.html` between Trends and Methodology | 2026-03-25 15:16 PST | 2026-03-25 15:17 PST |
| `[X]` | PE0-02 | Add `/pipeline` route to `app.py` returning `pipeline.html` via `base.html` wrapper | 2026-03-25 15:17 PST | 2026-03-25 15:17 PST |
| `[X]` | PE0-03 | Create `pipeline.html` template: full-width canvas container, control bar scaffold, detail panel placeholder, minimap placeholder | 2026-03-25 15:18 PST | 2026-03-25 15:18 PST |
| `[X]` | PE0-04 | Create empty `src/jobclass/web/static/js/pipeline_graph_data.js` scaffold with exported data structure stubs | 2026-03-25 15:19 PST | 2026-03-25 15:19 PST |
| `[X]` | PE0-05 | Create empty `src/jobclass/web/static/js/pipeline.js` scaffold with `DOMContentLoaded` entry point | 2026-03-25 15:19 PST | 2026-03-25 15:20 PST |
| `[X]` | PE0-06 | Add Pipeline Explorer CSS section to `main.css`: full-width layout override, canvas container, control bar, detail panel, minimap styles | 2026-03-25 15:20 PST | 2026-03-25 15:21 PST |
| `[X]` | PE0-07 | Bump cache-busting version in `base.html` (`?v=PE0`) | 2026-03-25 15:21 PST | 2026-03-25 15:21 PST |
| `[X]` | PE0-08 | Verify: page loads at `/pipeline` with nav highlighting and visible canvas area | 2026-03-25 15:21 PST | 2026-03-25 15:24 PST |

---

## Phase PE1: Graph Data Model

Populate `pipeline_graph_data.js` with the full graph: node types, edge types, lane groups, all nodes with metadata, all edges with conditions, and lesson anchor mappings. Content is mined from the real repository — README, specs, schema, CLI, and live pages.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE1-01 | Define node type constants: `source`, `process`, `storage`, `gate`, `interface`, `lesson` | 2026-03-25 15:25 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-02 | Define edge type constants: `required`, `conditional`, `blocked`, `optional`, `educational`, `derived` | 2026-03-25 15:25 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-03 | Define lane/group structure with labels, colors, and layout positions: Sources, Extraction, Raw, Staging, Validation, Core, Time-Series, Marts, API/Web, Deployment | 2026-03-25 15:25 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-04 | Add source nodes (SOC, OEWS, O\*NET, BLS Projections, CPI-U, SOC Crosswalk) with metadata: purpose, cadence, artifact type, key caveats | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-05 | Add extraction/acquisition nodes: download manager, run manifest, browser-header workaround, per-source downloaders | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-06 | Add raw landing nodes: immutable file storage per source with path pattern, checksum, and metadata fields | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-07 | Add staging/parsing nodes: per-dataset parsers (SOC hierarchy/definitions, OEWS national/state/metro/industry, O\*NET skills/knowledge/abilities/tasks/work-activities/education/technology, projections, CPI, crosswalk) | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-08 | Add validation gate nodes: schema drift detection, referential integrity, grain uniqueness, null semantics preservation, temporal consistency | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-09 | Add core warehouse nodes: `dim_occupation`, `dim_skill`, `dim_knowledge`, `dim_ability`, `dim_work_activity`, `dim_education_level`, `dim_technology_skill`, `dim_time_period`, fact tables, bridge tables | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-10 | Add time-series enrichment nodes: multi-vintage OEWS loading, CPI deflation (`CPI_BASE_YEAR = 2023`), derived series computation, comparable-history crosswalk logic | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-11 | Add mart nodes: occupation summary, wage comparison, trend analysis, time-series, and other analyst marts | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-12 | Add API/web/interface nodes: search, hierarchy browser, occupation profile, wage detail, trend explorer, occupation comparison, geography comparison, ranked movers, methodology, lessons landing, pipeline (self-referential) | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-13 | Add deployment/static nodes: `build_static.py`, fetch shim injection, `deploy_pages.py`, health check, `.nojekyll`, GitHub Pages | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-14 | Define all edges between nodes with type, direction, and condition labels (e.g., "SOC must load first", "schema drift blocks publication", "1:1 mappings only for wage comparison") | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE1-15 | Add lesson anchor mappings: map all 20 lessons to relevant graph node IDs (e.g., Lesson 1 → source group, Lesson 2 → four-layer architecture, Lesson 5 → time-series nodes, Lesson 7 → static generation, Lesson 13 → schema drift gate) | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |

---

## Phase PE2: Canvas Rendering Engine

Implement the core canvas rendering: initialization, DPI handling, render loop, lane backgrounds, node shapes by type, edge drawing, labels, and fit-to-screen.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE2-01 | Implement canvas initialization: create `<canvas>` element, handle device pixel ratio scaling, size to container | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-02 | Implement render loop with `requestAnimationFrame` and dirty-flag optimization | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-03 | Implement camera/transform state: offset (x, y), scale factor, world-to-screen and screen-to-world matrix transforms | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-04 | Implement lane/group background rendering: colored rectangular regions with centered group labels | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-05 | Implement node shape rendering by type: rounded rectangles (process/interface), hexagons (source), cylinders (storage), diamonds (gate), book icons (lesson) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-06 | Implement node label rendering with text measurement, wrapping, and scale-aware font sizing | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-07 | Implement edge rendering: polyline paths with directional arrowheads | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-08 | Implement edge style variants: solid (required), dashed (conditional), red (blocked), semi-transparent (optional), light dotted (educational), blue-tinted (derived) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-09 | Implement edge condition label rendering: short text centered on edge midpoint | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-10 | Implement status chip rendering on nodes: small colored badges for source/derived/conditional/optional/blocked/lesson-linked | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-11 | Implement fit-to-screen initial view: calculate graph bounding box, set transform to center and fit all content with padding | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE2-12 | Implement window resize handler: re-size canvas, maintain camera center, re-render | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |

---

## Phase PE3: Pan, Zoom & Camera

Implement all navigation inputs: mouse wheel zoom, click-drag pan, touch gestures, double-click dive, reset button, and smooth animated transitions.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE3-01 | Implement mouse wheel zoom anchored to pointer position (zoom toward/away from cursor) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE3-02 | Implement click-drag pan: `mousedown` → `mousemove` → `mouseup` with grab cursor | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE3-03 | Implement touch pinch-zoom (two-finger gesture with zoom center between fingers) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE3-04 | Implement touch single-finger pan | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE3-05 | Implement double-click to center and zoom on nearest node | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE3-06 | Implement "Reset View" button with animated transition back to fit-to-screen | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE3-07 | Implement zoom level indicator display (text or bar showing current scale) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE3-08 | Implement smooth animated transitions for all camera movements (ease-in-out interpolation) | | |
| `[X]` | PE3-09 | Implement zoom clamping: minimum scale (full overview) and maximum scale (detail level) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |

---

## Phase PE4: Semantic Zoom

Implement tiered zoom levels where deeper zoom reveals richer representations rather than only larger shapes.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PE4-01 | Define three zoom threshold breakpoints: overview (scale < 0.4), subsystem (0.4–1.2), detail (> 1.2) | | |
| `[ ]` | PE4-02 | Overview level rendering: show lane blocks only with aggregate labels and node counts per group | | |
| `[ ]` | PE4-03 | Subsystem level rendering: show individual nodes with names, type icons, and basic connections | | |
| `[X]` | PE4-04 | Detail level rendering: show full metadata, input/output ports, edge labels, and condition annotations | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE4-05 | Implement smooth crossfade between zoom levels (opacity transitions during threshold crossing) | | |
| `[X]` | PE4-06 | Implement progressive label disclosure: more text and metadata visible at deeper zoom | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE4-07 | Implement edge simplification at overview level: bundle edges between lanes into single aggregate arrows | | |
| `[ ]` | PE4-08 | Implement level-appropriate hit targets: larger clickable areas at overview, precise at detail | | |

---

## Phase PE5: Node Interaction — Hover & Select

Implement hit testing, hover tooltips, click selection, path highlighting, and dimming of unrelated nodes.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE5-01 | Implement point-in-node hit testing using screen-to-world coordinate transform and shape-aware bounds | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE5-02 | Implement hover detection with pointer cursor change on hoverable elements | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE5-03 | Implement hover tooltip: node name, type badge, one-line purpose — positioned near cursor | | |
| `[ ]` | PE5-04 | Implement tooltip positioning logic: clamp to canvas bounds, avoid edge clipping | | |
| `[X]` | PE5-05 | Implement click-to-select with visual highlight: border glow, raised appearance, color accent | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE5-06 | Implement upstream ancestry path highlighting on select: brighten all upstream nodes and edges | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE5-07 | Implement downstream descendant path highlighting on select: brighten all downstream nodes and edges | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE5-08 | Implement dim/fade for nodes and edges not in the selected node's ancestry or descendant paths | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE5-09 | Implement deselect on canvas background click (restore full graph visibility) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE5-10 | Implement edge hit testing and edge hover highlight (increase opacity/width on mouseover) | | |

---

## Phase PE6: Detail Panel

Implement the right-side drawer panel with tabbed sections for selected node/edge properties, metadata, related content, and jump-to links.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE6-01 | Create side drawer HTML structure: right-side panel with fixed position, slide-in/out animation, close button | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-02 | Implement drawer open on node select, close on deselect or close button, animate transitions | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-03 | Implement panel header: node title, type badge icon, one-line purpose | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-04 | Implement Overview section: "why it exists" paragraph, artifact type, upstream input count, downstream output count | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-05 | Implement Data section: inputs list, outputs list, key metadata (data grain, source version, refresh cadence, invariants) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-06 | Implement Interfaces section: related CLI commands, API endpoints, web pages, table names | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-07 | Implement Validation section: associated validation rules, failure modes, caveats (e.g., "5 NEM codes don't map to SOC 2018") | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-08 | Implement Lessons section: linked lesson cards with lesson number, title, and brief description | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE6-09 | Implement "Jump to" links: clickable links to methodology, lesson pages, occupation pages, or trends as appropriate | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE6-10 | Implement edge detail view: relationship meaning, condition text, type explanation, source/target node names | | |
| `[X]` | PE6-11 | Implement panel responsiveness: collapse to bottom sheet on narrow viewports (< 768px) | 2026-03-25 15:20 PST | 2026-03-25 15:21 PST |
| `[X]` | PE6-12 | Style panel with JobClass design language: CSS variables, consistent typography, compact and curated layout | 2026-03-25 15:20 PST | 2026-03-25 15:38 PST |

---

## Phase PE7: Minimap

Implement the overview minimap widget with viewport indicator and click-to-navigate.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE7-01 | Create minimap canvas element: corner overlay with compact fixed size and subtle border | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[X]` | PE7-02 | Render scaled-down version of entire graph on minimap (simplified: lane blocks + node dots) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE7-03 | Draw viewport rectangle on minimap showing the currently visible area | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE7-04 | Implement click-to-navigate: click on minimap pans main canvas to the clicked position | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE7-05 | Implement drag viewport rectangle on minimap to pan main canvas | | |
| `[X]` | PE7-06 | Update minimap rendering on every pan/zoom action | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE7-07 | Style minimap: semi-transparent background, intentional border, unobtrusive positioning | 2026-03-25 15:20 PST | 2026-03-25 15:21 PST |

---

## Phase PE8: Search, Filter & Controls

Implement the graph-specific control bar: search, type/domain filters, overlay toggles, path isolation, and reset.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE8-01 | Add search input with dropdown suggestions: search by node name, table name, page name, lesson title, or concept keyword | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[X]` | PE8-02 | Implement search result highlighting: matching nodes visually emphasized, camera pans to first match | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE8-03 | Add node type filter toggles: source, process, storage, gate, interface, lesson (multi-select) | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE8-04 | Add domain filter toggles: time-series, extraction, validation, deployment, lessons (multi-select) | | |
| `[X]` | PE8-05 | Implement filter logic: hide non-matching nodes and their disconnected edges, update minimap accordingly | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE8-06 | Add overlay toggles: validation paths, failure/blocked paths, lesson links, time-series branches | | |
| `[ ]` | PE8-07 | Implement overlay rendering: highlighted subgraph with distinct color per overlay type | | |
| `[ ]` | PE8-08 | Add "Isolate Path" action: from selected node, show only the connected path to a chosen target (or all reachable pages) | | |
| `[X]` | PE8-09 | Add "Reset Filters" button: clear all filters, overlays, and path isolation; return to full graph view | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[X]` | PE8-10 | Style control bar: compact horizontal bar above canvas, wraps responsively on narrow screens | 2026-03-25 15:20 PST | 2026-03-25 15:21 PST |

---

## Phase PE9: Guided Educational Modes

Implement four guided modes with step-by-step path tracing, annotations, and lesson links. Guided sequences are data-driven (defined in `pipeline_graph_data.js`), not hardcoded in the renderer.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE9-01 | Define guided mode data structure in `pipeline_graph_data.js`: array of modes, each with name, description, and sequence of steps (target node IDs, camera position, annotation text, lesson link) | 2026-03-25 15:30 PST | 2026-03-25 15:30 PST |
| `[X]` | PE9-02 | Implement mode selector UI: button group above canvas with mode names and brief descriptions | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-03 | Implement "Follow the Data" mode: step through source → Raw → Staging → Core → Marts → API → Pages, annotating each stage | 2026-03-25 15:30 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-04 | Implement "What Can Break" mode: highlight schema drift gate, unmapped SOC codes, suppressed OEWS values, comparability restrictions, publish gates | 2026-03-25 15:30 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-05 | Implement "Time-Series Path" mode: highlight multi-vintage OEWS, CPI deflation, crosswalk comparability, derived series, trend pages | 2026-03-25 15:30 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-06 | Implement "From Query to Proof" mode: start from a visible page or metric, trace backward through marts → facts → staging → sources | 2026-03-25 15:30 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-07 | Implement step-by-step progression: next/previous buttons, step counter (e.g., "Step 3 of 8") | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE9-08 | Implement animated path tracing: pulse animation along edges in the current step's path | | |
| `[X]` | PE9-09 | Implement step annotations: text callout positioned near the highlighted node with context description | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-10 | Implement lesson link display: show relevant lesson link at each step where a lesson is mapped | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE9-11 | Implement skip/exit mode: button to exit guided mode and return to free exploration | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE9-12 | Implement mode introduction overlay: brief description of the mode's purpose before the first step begins | | |

---

## Phase PE10: Animation & Visual Polish

Add subtle animations, flow effects, layer glows, micro-interactions, and reduced-motion support. Novelty through revealing structure, not visual noise.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PE10-01 | Add flow animation on data-flow edges: subtle moving dots/dashes suggesting directional data movement | | |
| `[X]` | PE10-02 | Add layer glow/halo for grouped zones: soft color tinting behind each lane (Raw, Staging, Core, Marts, Web) | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE10-03 | Add edge brightening on hover: increase opacity and width on mouseover, restore on mouseout | | |
| `[ ]` | PE10-04 | Add smooth camera transitions for all programmatic navigation (guided mode, search jump, reset) with ease-in-out | | |
| `[ ]` | PE10-05 | Add breadcrumb trail highlighting during drill-in: show visual path from overview to current focus | | |
| `[ ]` | PE10-06 | Add node entrance animation on first load: staggered fade-in with slight scale-up per lane group | | |
| `[ ]` | PE10-07 | Implement `prefers-reduced-motion` detection: disable all animations, use instant transitions when media query matches | | |
| `[ ]` | PE10-08 | Performance optimization: offscreen node culling, canvas draw call batching, throttle resize handler | | |

---

## Phase PE11: Cross-Links & Integration

Wire the Pipeline Explorer into existing Methodology and Lesson pages. Add deep-link support so nodes are addressable by URL.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PE11-01 | Add "View in Pipeline Explorer" link to `methodology.html` — deep-links to pipeline page with relevant lane focused | | |
| `[ ]` | PE11-02 | Add pipeline cross-reference links to lessons 1–5 templates (federal data, dimensional modeling, multi-vintage, data quality, time-series) | | |
| `[ ]` | PE11-03 | Add pipeline cross-reference links to lessons 6–10 templates (idempotent pipelines, static site, testing, similarity, thread safety) | | |
| `[ ]` | PE11-04 | Add pipeline cross-reference links to lessons 11–15 templates (multi-vintage queries, UI alignment, schema drift, inflation, taxonomy) | | |
| `[ ]` | PE11-05 | Add pipeline cross-reference links to lessons 16–20 templates (government APIs, derived metrics, outlier interpretation, geography pitfalls, fetch shim) | | |
| `[X]` | PE11-06 | Implement URL hash deep-linking: `/pipeline#node=<node_id>` focuses and selects the specified node on page load | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE11-07 | Implement "Copy link to this node" action in detail panel: copies deep-link URL to clipboard | | |
| `[X]` | PE11-08 | Add reverse links from pipeline node detail panel back to associated lesson/methodology/occupation pages | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE11-09 | Verify all cross-links navigate correctly in both directions (pipeline → lessons/methodology, lessons/methodology → pipeline) | | |

---

## Phase PE12: Accessibility

Ensure keyboard navigation, screen reader support, visible focus states, reduced-motion mode, and color contrast compliance.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PE12-01 | Implement keyboard navigation for control bar: Tab to cycle through search, filters, modes, and reset; Enter/Space to activate | | |
| `[ ]` | PE12-02 | Implement arrow-key traversal between graph nodes: follow edges directionally, wrap within groups | | |
| `[X]` | PE12-03 | Implement keyboard-accessible detail panel: Tab into panel sections, Escape to close | 2026-03-25 15:32 PST | 2026-03-25 15:38 PST |
| `[X]` | PE12-04 | Add visible focus indicators on all interactive elements (buttons, toggles, search input, canvas nodes) | 2026-03-25 15:20 PST | 2026-03-25 15:21 PST |
| `[X]` | PE12-05 | Add ARIA labels and roles: canvas (`role="img"` with `aria-label`), controls (`role="toolbar"`), detail panel (`role="complementary"`), minimap (`aria-label`) | 2026-03-25 15:18 PST | 2026-03-25 15:18 PST |
| `[X]` | PE12-06 | Add `aria-live` region for screen reader announcements on node selection, mode activation, and filter changes | 2026-03-25 15:18 PST | 2026-03-25 15:38 PST |
| `[ ]` | PE12-07 | Verify reduced-motion mode: confirm all animations disabled when `prefers-reduced-motion: reduce` is active | | |
| `[ ]` | PE12-08 | Validate color contrast ratios: all node type colors, edge colors, text, and interactive elements meet WCAG AA (4.5:1 for text, 3:1 for UI) | | |

---

## Phase PE13: Tests, Static Build & Deployment

Add automated tests, integrate with the static site builder, lint, and verify end-to-end.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | PE13-01 | Create `tests/web/test_pipeline.py` with `TestPipelinePage` class | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-02 | Test: `/pipeline` returns status 200 with correct page title | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-03 | Test: page HTML contains `<canvas>` element for graph rendering | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-04 | Test: page contains control bar markup with search input and filter controls | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-05 | Test: page contains guided mode button group with all four mode names | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-06 | Test: page contains detail panel structure (hidden by default) | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-07 | Test: nav bar "Pipeline" link is present and correctly placed on all pages | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-08 | Add `/pipeline` to HTML page generation in `build_static.py` | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-09 | Ensure `pipeline.js` and `pipeline_graph_data.js` are included in static asset output | 2026-03-25 15:45 PST | 2026-03-25 15:47 PST |
| `[X]` | PE13-10 | Run `ruff check src/ tests/` — all changed files pass linting | 2026-03-25 15:45 PST | 2026-03-25 15:48 PST |
| `[X]` | PE13-11 | Run full test suite (`pytest`) — all existing + new tests pass | 2026-03-25 15:45 PST | 2026-03-25 15:49 PST |
| `[ ]` | PE13-12 | Build static site (`build_static.py --base-path /jobclass`) and verify pipeline page renders at `/jobclass/pipeline` | | |

---

## Phase Summary

| Phase | Description | Tasks | Status |
|-------|-------------|-------|--------|
| PE0 | Infrastructure & Route Setup | 8 | Complete |
| PE1 | Graph Data Model | 15 | Complete |
| PE2 | Canvas Rendering Engine | 12 | Complete |
| PE3 | Pan, Zoom & Camera | 9 | In progress (8/9) |
| PE4 | Semantic Zoom | 8 | In progress (2/8) |
| PE5 | Node Interaction — Hover & Select | 10 | In progress (7/10) |
| PE6 | Detail Panel | 12 | In progress (10/12) |
| PE7 | Minimap | 7 | In progress (6/7) |
| PE8 | Search, Filter & Controls | 10 | In progress (6/10) |
| PE9 | Guided Educational Modes | 12 | In progress (10/12) |
| PE10 | Animation & Visual Polish | 8 | In progress (1/8) |
| PE11 | Cross-Links & Integration | 9 | In progress (2/9) |
| PE12 | Accessibility | 8 | In progress (4/8) |
| PE13 | Tests, Static Build & Deployment | 12 | In progress (11/12) |
| **Total** | | **140** | |

---

## Notes

- **PE0 must be done first.** It establishes the route, template, and file scaffolds all subsequent phases depend on.
- **PE1 should be done before PE2.** The rendering engine needs graph data to render. However, PE1 can be refined incrementally as later phases reveal needs.
- **PE2 through PE4 are sequential.** Each builds on the previous: basic rendering → navigation → semantic zoom.
- **PE5 and PE6 are sequential.** Hit testing and selection (PE5) must exist before the detail panel (PE6) can display anything.
- **PE7 and PE8 are independent** of each other and can be developed in either order after PE3 (both need pan/zoom to exist).
- **PE9 depends on PE5 + PE8.** Guided modes use selection, path highlighting, and overlay rendering.
- **PE10 can be interleaved** with other phases but should be finalized after PE9 to polish guided mode animations.
- **PE11 depends on PE6.** Cross-links require the detail panel and deep-link infrastructure to be in place.
- **PE12 should come after PE8.** Accessibility builds on all interactive controls being implemented.
- **PE13 depends on all prior phases.** This is the final integration gate.
- **Incremental deployment is encouraged.** After PE2, the page is visually useful. After PE6, it is functionally useful. Each milestone can be committed and deployed independently.
- **No third-party libraries.** All rendering, layout, animation, and interaction is vanilla Canvas API + vanilla JS, consistent with the rest of the project.
- **Graph data is static JS, not API-driven.** The graph model is a JS data file loaded at page init. No fetch calls needed for graph content. This ensures identical behavior on GitHub Pages and live server.
- **Lesson anchors cover all 20 lessons.** Each lesson is mapped to one or more graph nodes by ID. The mapping is defined in `pipeline_graph_data.js` and consumed by the detail panel and guided modes.

## Critical Files

| File | Action | Phase |
|------|--------|-------|
| `src/jobclass/web/app.py` | Add `/pipeline` route | PE0 |
| `src/jobclass/web/templates/pipeline.html` | New template | PE0 |
| `src/jobclass/web/templates/base.html` | Add nav link, bump cache version | PE0 |
| `src/jobclass/web/static/js/pipeline_graph_data.js` | New — full graph data model | PE1 |
| `src/jobclass/web/static/js/pipeline.js` | New — rendering engine, interaction, modes | PE2–PE10 |
| `src/jobclass/web/static/css/main.css` | Add Pipeline Explorer CSS section | PE0, PE6, PE10 |
| `src/jobclass/web/templates/methodology.html` | Add cross-link to pipeline | PE11 |
| `src/jobclass/web/templates/lessons_*.html` | Add cross-links (20 templates) | PE11 |
| `scripts/build_static.py` | Add pipeline page generation | PE13 |
| `tests/web/test_pipeline.py` | New — pipeline page tests | PE13 |
