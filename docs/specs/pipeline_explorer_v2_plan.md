# Phased Release Plan — Pipeline Explorer V2

This document tracks the work required to implement the seven improvements described in `pipeline_explorer_design_v2.md`. These changes transform the Pipeline Explorer's overview from a 4×2 card grid into a directed pipeline flow with focus+context drill-in, breadcrumb navigation, branching topology, flow animation, a subsystem zoom level, and zoom-aware guided modes.

All changes build on the completed v1 implementation (140/140 tasks, PE0–PE13). No v1 functionality is removed; the v2 work replaces the overview rendering and adds new intermediate states.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

## How To Use This Document

Use this document as a work queue, managing the Status of each item according to the status key. Started and Completed columns are datetimes in PST.
Always assign a task a status of [>] before beginning work. Mark work as complete [X] when it is complete. This is the central file that will show status, and tell you which items to work next.

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase PEv2-1: Overview Flow Layout & Topology

Replace the 4×2 card grid with a left-to-right directed flow graph. Add `SUMMARY_TOPOLOGY` data defining the branching connections between summary groups. Rewrite the overview layout engine to position blocks topologically and draw Bézier arrows for branches.

**Entry criteria**: V1 Pipeline Explorer complete (PE0–PE13 all `[X]`).

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-101 | Add `SUMMARY_TOPOLOGY` array to `pipeline_graph_data.js`: 9 edges with from/to/type/label fields defining the real pipeline branching structure | | |
| `[ ]` | PEv2-102 | Add `summaryTopology: SUMMARY_TOPOLOGY` to the `PIPELINE_GRAPH` export object | | |
| `[ ]` | PEv2-103 | Rewrite `computeSummaryBlocks()`: replace 4×2 grid layout with topological sort-based horizontal positioning; blocks at same rank stack vertically | | |
| `[ ]` | PEv2-104 | Compute Bézier control points for branch arrows at init time; store on each topology edge for reuse during rendering | | |
| `[ ]` | PEv2-105 | Rewrite `drawOverviewArrows()`: draw straight arrows for main-spine edges, quadratic Bézier curves for branch edges, dashed style for conditional edges | | |
| `[ ]` | PEv2-106 | Add condition labels on conditional topology arrows (e.g., "gates pass" on validate→warehouse) | | |
| `[ ]` | PEv2-107 | Rewrite `drawOverviewBlock()`: replace card-style rendering with compact pipeline-block style — accent left border, title, subtitle (2-line purpose), node count badge | | |
| `[ ]` | PEv2-108 | Update `getOverviewBounds()` and `fitOverview()` to fit the new topological layout instead of 4×2 grid | | |
| `[ ]` | PEv2-109 | Update `hitTestSummaryBlock()` for new block positions and sizes (220×140 world units) | | |
| `[ ]` | PEv2-110 | Update overview hover rendering for new block style: 1.03× scale-up, shadow depth increase, accent border widening | | |
| `[ ]` | PEv2-111 | Verify overview keyboard navigation (arrow keys) works with topological layout: Left/Right follow main spine, Up/Down switch between vertically-stacked blocks | | |
| `[ ]` | PEv2-112 | Run all tests, verify lint clean | | |

---

## Phase PEv2-2: Flow Animation in Overview

Add subtle directional dot animation to overview arrows. Dots travel along each arrow path indicating data flow direction.

**Entry criteria**: PEv2-1 complete (topological layout and Bézier arrows in place).

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-201 | Add overview flow animation state: per-edge dot phase counter, dot count (2–3 per arrow), speed (40px/sec) | | |
| `[ ]` | PEv2-202 | Implement dot position calculation along straight arrows: lerp from source to target block edges | | |
| `[ ]` | PEv2-203 | Implement dot position calculation along Bézier arrows: evaluate quadratic Bézier at parameterized t values | | |
| `[ ]` | PEv2-204 | Render flow dots in `drawOverviewArrows()`: 3px radius circles at 50% of arrow accent color | | |
| `[ ]` | PEv2-205 | Integrate with existing `flowPhase` timer so overview and detail flow animations share the same clock | | |
| `[ ]` | PEv2-206 | Respect `prefers-reduced-motion`: skip dot rendering and animation when reduced motion is preferred | | |
| `[ ]` | PEv2-207 | Pause animation when `document.hidden` is true (tab not visible) to save CPU | | |
| `[ ]` | PEv2-208 | Run all tests, verify lint clean | | |

---

## Phase PEv2-3: Focus+Context Drill-In

Replace the binary `drillGroup` hide/show filter with a three-tier visibility model: focused stage at full brightness, adjacent stages dimmed, distant stages nearly invisible. The user never loses context about where the focused stage sits.

**Entry criteria**: PEv2-1 complete (topological layout provides adjacency information).

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-301 | Add `getGroupAdjacency(groupId)` function: uses `SUMMARY_TOPOLOGY` to return sets of adjacent and distant group IDs | | |
| `[ ]` | PEv2-302 | Add `getNodeVisibilityTier(node)` function: returns `"focus"`, `"adjacent"`, or `"distant"` based on drillGroup and adjacency | | |
| `[ ]` | PEv2-303 | Modify `isNodeVisible()`: always return true when a drillGroup is set (no longer hide non-group nodes); downstream code uses visibility tier for rendering decisions | | |
| `[ ]` | PEv2-304 | Modify `drawLanes()`: draw all lanes but apply tier-based opacity (100% focus, 25% adjacent, 8% distant) | | |
| `[ ]` | PEv2-305 | Modify `drawNodes()` / `drawNode()`: apply tier-based opacity to fill, border, and label (see design doc Section 6.3) | | |
| `[ ]` | PEv2-306 | Modify `drawEdges()` / `drawEdge()`: apply tier-based opacity; hide edge labels for adjacent tier, hide edges entirely for distant tier | | |
| `[ ]` | PEv2-307 | Update `drillIntoGroup()`: set camera to frame focused group + partial adjacent groups (20% of adjacent width visible) | | |
| `[ ]` | PEv2-308 | Implement click-on-adjacent-stage: clicking a dimmed adjacent stage shifts focus to it (re-centers camera, updates tiers) | | |
| `[ ]` | PEv2-309 | Update minimap rendering to reflect focus+context opacity tiers | | |
| `[ ]` | PEv2-310 | Update screen reader announcements: announce focused stage name and "adjacent stages visible" on drill-in | | |
| `[ ]` | PEv2-311 | Run all tests, verify lint clean | | |

---

## Phase PEv2-4: Breadcrumb Navigation

Add a horizontal breadcrumb bar showing the current navigation path: Pipeline Overview → Stage → Node. Each segment is clickable.

**Entry criteria**: PEv2-3 complete (focus+context provides the stage-level navigation that breadcrumbs describe).

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-401 | Add breadcrumb `<nav>` element to `pipeline.html`: `<nav aria-label="Breadcrumb" class="pipeline-breadcrumb">` with `<ol>` container, placed between control bar and canvas wrapper | | |
| `[ ]` | PEv2-402 | Add breadcrumb CSS to `main.css`: 32px height bar, `#f8fafc` background, chevron separators, accent-colored current segment, underline-on-hover for clickable segments | | |
| `[ ]` | PEv2-403 | Implement `updateBreadcrumb()` function: reads `viewMode`, `drillGroup`, and `selectedNode` to generate breadcrumb segments | | |
| `[ ]` | PEv2-404 | Wire breadcrumb updates into all navigation events: `drillIntoGroup()`, `returnToOverview()`, node selection, node deselection, guided mode steps | | |
| `[ ]` | PEv2-405 | Implement breadcrumb click handlers: "Pipeline Overview" → `returnToOverview()`, stage name → `drillIntoGroup(stage)` with node deselected, node name → no-op (already there) | | |
| `[ ]` | PEv2-406 | Add breadcrumb segment entrance animation: new segments slide in from right with 200ms ease-out (skip if reduced-motion) | | |
| `[ ]` | PEv2-407 | Hide breadcrumb bar when `data-view-mode="overview"` (breadcrumb is redundant at top level) via CSS rule | | |
| `[ ]` | PEv2-408 | Add ARIA attributes: `aria-current="page"` on the last breadcrumb segment, screen reader announces breadcrumb updates | | |
| `[ ]` | PEv2-409 | Add test: breadcrumb `<nav>` element exists in pipeline page HTML | | |
| `[ ]` | PEv2-410 | Run all tests, verify lint clean | | |

---

## Phase PEv2-5: Subsystem Zoom Level

Add an intermediate view between overview blocks and full node-level detail. Clicking a summary block first shows the subsystem view: the focused block expands to reveal node names in a compact grid, with adjacent blocks dimmed.

**Entry criteria**: PEv2-3 complete (focus+context renders adjacent stages), PEv2-4 complete (breadcrumb reflects navigation state).

**Depends on**: PEv2-3 (focus+context), PEv2-4 (breadcrumb)

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-501 | Add `"subsystem"` to the `viewMode` state options (currently `"overview"` or `"detail"`) | | |
| `[ ]` | PEv2-502 | Implement `computeSubsystemLayout(group)`: arrange group's nodes as labeled boxes in a compact grid within the expanded block boundary; return array of `{ node, x, y, w, h }` | | |
| `[ ]` | PEv2-503 | Implement `drawSubsystem()`: render expanded block with node-name boxes (simplified rectangles + text + type icon, no full shape variants) | | |
| `[ ]` | PEv2-504 | Draw intra-group edges in subsystem view: simple arrows between node boxes within the expanded block | | |
| `[ ]` | PEv2-505 | Draw cross-group edge stubs: arrows from node boxes that point outward to adjacent blocks, terminating at the expanded block boundary | | |
| `[ ]` | PEv2-506 | Render adjacent blocks at focus+context opacity (reuse PEv2-3 tier rendering) in subsystem view | | |
| `[ ]` | PEv2-507 | Modify click handler: in overview, click block → enter subsystem view; in subsystem, click node → enter detail view for that node; in subsystem, click background → return to overview | | |
| `[ ]` | PEv2-508 | Modify double-click handler: in overview, double-click block → skip subsystem, go directly to detail view | | |
| `[ ]` | PEv2-509 | Implement block expansion animation: summary block smoothly grows from overview size to subsystem size over 400ms (crossfade content during transition) | | |
| `[ ]` | PEv2-510 | Modify wheel handler: zoom in past subsystem threshold → transition to detail; zoom out past subsystem threshold → transition to overview | | |
| `[ ]` | PEv2-511 | Implement `hitTestSubsystemNode(wx, wy)`: hit test node boxes within the expanded block | | |
| `[ ]` | PEv2-512 | Update Escape key behavior: in subsystem → return to overview; in detail → return to subsystem (instead of overview) | | |
| `[ ]` | PEv2-513 | Update keyboard arrow navigation: in subsystem, arrows cycle between node boxes within the expanded block | | |
| `[ ]` | PEv2-514 | Update `data-view-mode` attribute on `.pipeline-page`: support `"subsystem"` value; update CSS visibility rules for subsystem mode | | |
| `[ ]` | PEv2-515 | Update breadcrumb for subsystem view: show "Pipeline Overview > [Stage Name]" | | |
| `[ ]` | PEv2-516 | Update minimap to reflect subsystem view state | | |
| `[ ]` | PEv2-517 | Update screen reader announcements for subsystem entry/exit | | |
| `[ ]` | PEv2-518 | Add test: `data-view-mode` attribute supports `"subsystem"` value | | |
| `[ ]` | PEv2-519 | Run all tests, verify lint clean | | |

---

## Phase PEv2-6: Zoom-Aware Guided Modes

Redesign the four guided modes to work across zoom levels. Steps specify their target zoom level (overview, subsystem, or detail) and the engine animates between levels as the user progresses.

**Entry criteria**: PEv2-5 complete (subsystem zoom level exists).

**Depends on**: PEv2-5 (subsystem view)

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-601 | Extend guided mode step schema in `pipeline_graph_data.js`: add `targetZoom` field (`"overview"`, `"subsystem"`, `"detail"`) and `targetGroup` field to each step | | |
| `[ ]` | PEv2-602 | Revise "Follow the Data" mode steps: start at overview (full pipeline), progress through subsystem views of key stages, drill into detail for `dim_occupation` | | |
| `[ ]` | PEv2-603 | Revise "What Can Break" mode steps: overview shows gate positions, subsystem shows validation nodes, detail shows specific failure modes | | |
| `[ ]` | PEv2-604 | Revise "Time-Series Path" mode steps: overview highlights the time-series branch, subsystem shows enrichment nodes, detail shows CPI deflation | | |
| `[ ]` | PEv2-605 | Revise "From Query to Proof" mode steps: start at detail (a web page node), zoom out to subsystem, then overview to show the full provenance chain | | |
| `[ ]` | PEv2-606 | Modify guided mode engine: on step change, check `targetZoom` and transition to the correct view mode before animating camera to the target | | |
| `[ ]` | PEv2-607 | Implement cross-zoom transitions in guided mode: if current zoom differs from target zoom, chain the mode transition with the camera animation (mode transition first, then camera pan) | | |
| `[ ]` | PEv2-608 | Update guided step overlay positioning for subsystem view: overlay floats near expanded block, not at fixed screen position | | |
| `[ ]` | PEv2-609 | Update guided mode intro overlay to describe the zoom-progressive experience: "This tour will guide you from the big picture down to specific components" | | |
| `[ ]` | PEv2-610 | Verify guided mode pulse animation works across all zoom levels (overview: pulse on summary block, subsystem: pulse on node box, detail: pulse on full node) | | |
| `[ ]` | PEv2-611 | Update screen reader announcements for guided steps: announce zoom level change alongside step content | | |
| `[ ]` | PEv2-612 | Run all tests, verify lint clean | | |

---

## Phase PEv2-7: Tests, Polish & Deployment

Final integration testing, visual polish, performance verification, static site build, and deployment.

**Entry criteria**: PEv2-1 through PEv2-6 all complete.

**Depends on**: All prior phases.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[ ]` | PEv2-701 | Add test: `SUMMARY_TOPOLOGY` referenced in `pipeline_graph_data.js` static asset | | |
| `[ ]` | PEv2-702 | Add test: breadcrumb nav element exists in pipeline page HTML | | |
| `[ ]` | PEv2-703 | Add test: `data-view-mode` attribute present on `.pipeline-page` with default value | | |
| `[ ]` | PEv2-704 | Add test: guided mode steps include `targetZoom` field (validate graph data structure) | | |
| `[ ]` | PEv2-705 | Verify all 22 existing pipeline tests still pass (no regressions) | | |
| `[ ]` | PEv2-706 | Run full test suite (`pytest tests/unit/ tests/web/`) — all tests pass | | |
| `[ ]` | PEv2-707 | Run `ruff check src/ tests/` — all files lint clean | | |
| `[ ]` | PEv2-708 | Performance check: overview flow animation maintains 60fps on canvas at default window size | | |
| `[ ]` | PEv2-709 | Performance check: subsystem view with largest group (serve: 19 nodes) renders without jank | | |
| `[ ]` | PEv2-710 | Verify `prefers-reduced-motion` disables all new animations (flow dots, breadcrumb slide, block expansion) | | |
| `[ ]` | PEv2-711 | Verify keyboard navigation through all three zoom levels: overview → subsystem → detail and back | | |
| `[ ]` | PEv2-712 | Verify URL hash deep-linking (`#node=ID`) correctly enters detail mode through subsystem | | |
| `[ ]` | PEv2-713 | Verify search from overview: selecting a search result drills through subsystem into detail for the target node | | |
| `[ ]` | PEv2-714 | Bump cache-busting version in `base.html` (`?v=PEv2`) | | |
| `[ ]` | PEv2-715 | Build static site (`MSYS_NO_PATHCONV=1 python scripts/build_static.py --base-path /jobclass`) and verify pipeline page renders | | |
| `[ ]` | PEv2-716 | Visual walkthrough: verify overview flow layout, topology arrows, flow animation, drill-in with context, breadcrumb, subsystem view, guided modes across zoom levels | | |

---

## Phase Summary

| Phase | Description | Tasks | Status |
|-------|-------------|-------|--------|
| PEv2-1 | Overview Flow Layout & Topology | 12 | Not started |
| PEv2-2 | Flow Animation in Overview | 8 | Not started |
| PEv2-3 | Focus+Context Drill-In | 11 | Not started |
| PEv2-4 | Breadcrumb Navigation | 10 | Not started |
| PEv2-5 | Subsystem Zoom Level | 19 | Not started |
| PEv2-6 | Zoom-Aware Guided Modes | 12 | Not started |
| PEv2-7 | Tests, Polish & Deployment | 16 | Not started |
| **Total** | | **88** | |

---

## Dependency Graph

```
PEv2-1 (Flow Layout)
  ├── PEv2-2 (Flow Animation)     [needs Bézier arrows from PEv2-1]
  └── PEv2-3 (Focus+Context)     [needs topology adjacency from PEv2-1]
        └── PEv2-4 (Breadcrumb)   [needs stage navigation from PEv2-3]
              └── PEv2-5 (Subsystem Zoom) [needs focus+context + breadcrumb]
                    └── PEv2-6 (Guided Modes) [needs all three zoom levels]
                          └── PEv2-7 (Tests & Deploy) [needs all features]
```

PEv2-2 (Flow Animation) is independent of PEv2-3 through PEv2-6 and can be developed in parallel with PEv2-3.

## Notes

- **No v1 features are removed.** The v2 work replaces overview rendering and adds intermediate states; all existing detail mode functionality (filters, overlays, search, minimap, detail panel, guided modes) continues to work.
- **No third-party libraries.** All new rendering (Bézier arrows, flow dots, subsystem grid, breadcrumb) is vanilla Canvas API + vanilla JS + vanilla CSS.
- **Graph data is static JS, not API-driven.** The new `SUMMARY_TOPOLOGY` is a static JS array in `pipeline_graph_data.js`, consistent with the existing approach.
- **Incremental deployment is encouraged.** After PEv2-1, the overview is already improved (flow layout vs. grid). After PEv2-3, drill-in is substantially better. Each phase can be committed and deployed independently.
- **Subsystem view (PEv2-5) is the largest phase.** It introduces a third view mode and requires changes to click handling, keyboard navigation, transitions, minimap, and breadcrumb. Plan extra time.
- **Guided mode revision (PEv2-6) touches data and engine.** The step schema change in `pipeline_graph_data.js` means all four modes' step arrays are rewritten. The engine changes in `pipeline.js` add zoom-level targeting to the step progression logic.

## Critical Files

| File | Action | Phases |
|------|--------|--------|
| `src/jobclass/web/static/js/pipeline_graph_data.js` | Add `SUMMARY_TOPOLOGY`, extend guided mode steps | PEv2-1, PEv2-6 |
| `src/jobclass/web/static/js/pipeline.js` | Rewrite overview layout, add focus+context, subsystem view, breadcrumb logic, revised guided engine | PEv2-1 through PEv2-6 |
| `src/jobclass/web/templates/pipeline.html` | Add breadcrumb `<nav>` element | PEv2-4 |
| `src/jobclass/web/static/css/main.css` | Breadcrumb styles, subsystem visibility rules | PEv2-4, PEv2-5 |
| `src/jobclass/web/templates/base.html` | Bump cache version | PEv2-7 |
| `tests/web/test_pipeline.py` | New test assertions for topology, breadcrumb, view modes | PEv2-7 |
