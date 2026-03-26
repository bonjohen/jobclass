# Pipeline Explorer Design V2 — Semantic Zoom & Focus+Context

This document describes the second iteration of the Pipeline Explorer, building on the completed v1 implementation (140/140 tasks, PE0–PE13). The v1 delivery produced a canvas-based interactive graph with 57 nodes, 100+ edges, 10 lane groups, guided educational modes, detail panels, minimap, search/filter/overlays, and accessibility support. This iteration addresses seven gaps between the v1 outcome and the original design vision in `pipeline_explorer_design.md`.

## 1. Design Motivation

The v1 Pipeline Explorer has two modes: an overview showing 8 summary cards in a 4×2 grid, and a detail mode that filters to a single stage's nodes. While functional, this falls short of the original spec in several ways:

- The overview is a **card grid**, not a **pipeline flow**. It does not communicate directionality, branching, or topology. A visitor cannot see that data moves left to right, that validation gates block forward progress, or that time-series enrichment is a side path off the core warehouse.

- Drill-in **hides** all surrounding stages. The user loses context about where the focused stage sits in the pipeline. The original spec (Section 5) requires "overview+detail and focus+context so the visitor never loses their place while drilling deeper."

- There is **no breadcrumb**. The original spec (Section 5) calls for "breadcrumbs, highlighted ancestry, and a stable visual layout" during drill-in.

- The overview shows **linear sequential arrows** between cards. The real pipeline has branches (time-series, CPI adjustment, crosswalk), gates (validation blocks publication), and merge points (marts aggregate from multiple upstream paths). These are invisible at the overview level.

- Overview arrows are **static**. The original spec (Section 13) calls for "subtle animated pulses on active paths" and "flow animation" to make the page feel alive.

- There is **no intermediate zoom level**. The original spec (Section 6) describes four levels: overview → subsystem → detail → properties. The current implementation jumps from 8 summary blocks directly to individual nodes. The subsystem level — where blocks expand to show node names but not full metadata — is missing.

- **Guided modes ignore zoom level**. All four guided modes immediately switch to full detail view. The original spec envisions guided exploration that starts at the overview and progressively zooms in, matching the educational principle of moving from context to specifics.

## 2. Design Principles

These principles govern all v2 changes:

**Flow over layout.** The overview must read as a directed pipeline, not a dashboard of cards. Left-to-right flow with explicit arrows communicates causality and sequence.

**Context over isolation.** Drilling in should dim, not destroy, the surrounding pipeline. The focused stage is bright and detailed; neighboring stages are visible at reduced intensity. The user always knows where they are.

**Progressive disclosure over mode switches.** Moving from overview to subsystem to detail should feel like continuous zooming into the same space, not switching between different screens.

**Topology over simplification.** The overview should show the real shape of the pipeline: branches, gates, merge points, and optional paths. Simplification hides the most interesting structural properties.

**Motion for meaning.** Flow animation on arrows communicates data direction. Pulse animation on active paths communicates selection. Animation serves understanding, not decoration.

## 3. Current State (V1 Baseline)

The v1 Pipeline Explorer provides:

- **8 summary groups**: acquire, land, parse, validate, warehouse, timeseries, serve, deploy
- **Two view modes**: `overview` (card grid) and `detail` (filtered nodes within one stage)
- **Overview rendering**: 4×2 grid of 250×260px cards with purpose text, bulleted items, and accent colors
- **Overview arrows**: Sequential left-to-right within rows, downward wrap between rows
- **Drill-in**: Click a card → camera animates to the stage's lane region, all other stages hidden via `drillGroup` filter
- **Crossfade transition**: 400ms opacity transition between modes
- **Camera system**: `{ x, y, scale }` with easeInOutCubic animation
- **All v1 features intact**: Minimap, search, filters, overlays, guided modes, detail panel, accessibility, keyboard navigation, URL hash deep-linking

## 4. Target State (V2)

### 4.1 Overview as Pipeline Flow

Replace the 4×2 card grid with a **left-to-right directed flow graph** where each summary block is a node in a topological layout.

The 8 summary blocks retain their existing content (label, purpose, accent color, items list) but are positioned to reflect the actual pipeline topology:

```
                    ┌───────────┐
┌────────┐  ┌─────┐│ Validation │  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐
│ Sources ├──► Raw ├┤   Gates   ├──► Core       ├──► Marts &   ├──► Build &  │  │        │
│         │  │     ││           │  │ Warehouse  │  │ Web       │  │ Deploy   │  │        │
└────┬───┘  └─────┘└───────────┘  └─────┬──────┘  └───────────┘  └──────────┘  │        │
     │                                   │                                      │        │
     │      ┌──────────┐                 │         ┌───────────┐                │        │
     └──────► Stage &  ├─────────────────┘         │Time-Series├────────────────┘        │
             │ Parse   │                            └───────────┘                         │
             └─────────┘
```

Key topology features visible at overview:

- **Main spine**: Sources → Raw → Validation → Core → Marts & Web → Deploy
- **Parsing branch**: Sources also feeds into Stage & Parse, which feeds Core directly (parsed data enters through validation)
- **Time-series side path**: Core branches into Time-Series enrichment, which feeds back into Marts & Web
- **Validation as a gate**: Sits between raw/parsed data and the warehouse, visually blocking forward progress

Block layout uses world coordinates in the same coordinate space as the detail view, enabling natural zoom transitions. Blocks are sized 220×140px in world units, spaced with 60px horizontal gaps and 40px vertical gaps for branches.

### 4.2 Focus+Context Drill-In

When the user clicks a summary block (or zooms into a region):

- The **focused stage** renders at full brightness: all nodes, edges, labels, lane background at 100% opacity.
- **Adjacent stages** (directly connected upstream/downstream) render at 30% opacity: lane backgrounds visible, node outlines visible, labels visible but dimmed.
- **Distant stages** (two or more hops away) render at 10% opacity: lane backgrounds only, no individual node rendering.
- The **camera frames the focused stage** with enough margin to show adjacent stages in peripheral vision.

This replaces the current binary `drillGroup` filter. Instead of `isNodeInDrillGroup()` returning false for non-group nodes, it will return a **visibility tier**: `"focus"`, `"adjacent"`, or `"distant"`. Rendering functions use this tier to select opacity and detail level.

The user can:
- Click an adjacent (dimmed) stage to shift focus to it
- Click the focused stage's background to zoom into individual nodes
- Press Escape or click the Overview breadcrumb to return to the full overview

### 4.3 Breadcrumb Navigation Bar

Add a horizontal breadcrumb bar between the control bar and the canvas:

```
Pipeline Overview  >  Core Warehouse  >  dim_occupation
```

Each segment is clickable:
- **"Pipeline Overview"** always present; clicking it returns to the overview flow
- **Stage name** appears when drilled into a stage; clicking returns to stage focus view
- **Node name** appears when a specific node is selected; clicking deselects the node but keeps stage focus

The breadcrumb updates on every navigation event: drill-in, drill-out, node selection, guided mode step change. It provides persistent orientation even when the user is deep in the graph.

Implementation: A `<nav>` element with `aria-label="Breadcrumb"` containing an `<ol>` with `<li>` items. CSS uses the pipeline accent color system. The breadcrumb is hidden in overview mode (only "Pipeline Overview" is shown, which is redundant with the page title).

### 4.4 Branching Topology in Overview

The overview arrows currently connect blocks sequentially: block 0→1→2→3→4→5→6→7. The real pipeline has branching topology that should be visible.

Define explicit topology connections between summary groups:

| From | To | Type | Label |
|------|----|------|-------|
| acquire | land | required | — |
| acquire | parse | required | — |
| land | validate | required | — |
| parse | validate | required | — |
| validate | warehouse | conditional | "gates pass" |
| warehouse | timeseries | required | — |
| warehouse | serve | required | — |
| timeseries | serve | required | "enriched marts" |
| serve | deploy | required | — |

This topology shows:
- Sources feed **both** Raw Landing and Stage & Parse (parallel acquisition paths)
- Both raw and parsed data converge at Validation
- Validation is a **gate** — the label "gates pass" communicates conditional flow
- Core Warehouse branches into both Time-Series and Marts (parallel consumption)
- Time-Series feeds back into Marts (enriched data joins base marts)

Overview arrows use quadratic Bézier curves for branches (not straight lines) to make topology readable. The main spine uses straight horizontal arrows; branches use gentle curves that drop below or rise above the spine.

### 4.5 Flow Animation in Overview

Add subtle directional animation to overview arrows: small dots (3px radius) traveling along each arrow path at ~40px/second. This communicates data direction without being distracting.

- Dots are rendered at 50% of the arrow's accent color
- Each arrow has 2–3 dots evenly spaced along its length
- Animation uses `requestAnimationFrame` and the existing `flowPhase` timer
- Animation respects `prefers-reduced-motion`: disabled when reduced motion is preferred
- Animation pauses when the tab is not visible (uses `document.hidden`)

### 4.6 Subsystem Zoom Level

Add an intermediate view between the 8-block overview and full node-level detail. When the user clicks a summary block, instead of jumping directly to individual nodes, first show the **subsystem view**:

**Subsystem view characteristics:**
- The focused block **expands** to reveal its constituent nodes as labeled boxes (name + type icon only, no metadata)
- Node boxes are arranged in a compact grid within the expanded block boundary
- Edges between nodes within the block are shown as simple arrows
- Cross-block edges (connections to other stages) terminate at the block boundary with an arrow pointing outward
- Adjacent blocks remain visible at reduced opacity (focus+context)
- The camera frames the expanded block with margin

**Subsystem → Detail transition:**
- Click a specific node within the expanded block → zoom to that node, show full metadata, open detail panel
- Double-click the expanded block background → zoom to show all nodes at full detail level
- Zoom in with scroll wheel → progressive transition from subsystem to detail level

**Subsystem ← Overview transition:**
- Click the expanded block again → collapse back and return to overview
- Press Escape → return to overview
- Click breadcrumb "Pipeline Overview" → return to overview

The subsystem level bridges the gap between "I see 8 pipeline stages" and "I see 57 individual nodes." It answers the question "what's inside this stage?" without overwhelming with full metadata.

### 4.7 Zoom-Aware Guided Modes

Redesign the four guided modes to work across zoom levels rather than immediately jumping to detail view.

**Revised guided mode step structure:**

Each step in a guided mode sequence specifies:
- `targetZoom`: `"overview"`, `"subsystem"`, or `"detail"` — the zoom level for this step
- `targetGroup`: summary group ID (for overview/subsystem steps)
- `targetNode`: node ID (for detail steps)
- `annotation`: step description text
- `lessonLink`: optional lesson page link

**Example: "Follow the Data" revised sequence:**

| Step | Zoom Level | Target | Annotation |
|------|-----------|--------|------------|
| 1 | overview | (all) | "This is the complete JobClass pipeline — 8 stages from raw data to deployed website." |
| 2 | overview | acquire | "It starts here: 6 federal data products downloaded with browser-header workarounds." |
| 3 | subsystem | acquire | "Each source has its own downloader. SOC must complete first — it's the taxonomy backbone." |
| 4 | overview | validate | "All parsed data passes through validation gates before entering the warehouse." |
| 5 | subsystem | validate | "Five gate types: schema drift, referential integrity, grain uniqueness, null semantics, temporal consistency." |
| 6 | overview | warehouse | "The core warehouse holds conformed dimensions, facts, and bridges." |
| 7 | detail | dim_occupation | "dim_occupation is the central dimension — occupation is the stable external key." |
| 8 | overview | serve | "Marts power the web pages you're browsing right now." |

This progression teaches at the right level of abstraction for each concept:
- System-level concepts (the overall flow) use overview
- Stage-level concepts (what's inside a stage) use subsystem
- Specific technical details (a particular table or gate) use detail

The guided mode engine animates between zoom levels using the existing crossfade transition system, creating a smooth cinematic experience rather than jarring mode switches.

## 5. Interaction Model Summary

### 5.1 Zoom Level Hierarchy

| Level | What's Visible | How to Enter | How to Exit |
|-------|---------------|--------------|-------------|
| Overview | 8 summary blocks in pipeline flow, animated arrows, branching topology | Page load, Reset button, breadcrumb "Overview", Escape from subsystem | Click a block → subsystem |
| Subsystem | Focused block expanded with node names, adjacent blocks dimmed | Click a block in overview | Click a node → detail; Escape → overview |
| Detail | Full node rendering within focused stage, metadata labels, edge conditions | Click a node in subsystem, or double-click a block | Escape → subsystem; breadcrumb → any level |
| Properties | Detail panel open for selected node/edge | Click a node in detail mode | Close panel button, Escape, click background |

### 5.2 Navigation Actions

| Action | In Overview | In Subsystem | In Detail |
|--------|------------|-------------|-----------|
| Click block | Drill to subsystem | Shift focus to clicked block | — |
| Click node | — | Drill to detail, select node | Select/deselect node |
| Click background | — | Return to overview | Deselect node |
| Double-click block | Drill to detail (skip subsystem) | Zoom to full detail | — |
| Scroll zoom in | Animate to subsystem of nearest block | Transition to detail level | Normal zoom |
| Scroll zoom out | Normal zoom (clamped) | Return to overview below threshold | Return to subsystem below threshold |
| Escape | — | Return to overview | Return to subsystem |
| Arrow keys | Cycle between blocks | Cycle between nodes in block | Move to adjacent node |
| Enter | Drill into focused block | Select focused node | Open detail panel |

### 5.3 Camera Behavior

All camera transitions use easeInOutCubic interpolation over 400ms (or instant for reduced-motion users).

- **Overview**: Camera fits all 8 blocks with 60px padding
- **Subsystem**: Camera frames focused block + partial adjacent blocks (20% of adjacent width visible)
- **Detail**: Camera frames focused block's lane region at 1:1 scale
- **Node focus**: Camera centers on selected node at scale 1.5

## 6. Visual Design

### 6.1 Overview Block Styling

Each summary block in the overview flow is rendered as a rounded rectangle (12px radius) with:
- **Accent-colored left border** (4px): Uses the group's accent color for quick identification
- **White/dark fill**: Adapts to match the site's light background
- **Title** (16px bold): Group label (e.g., "Core Warehouse")
- **Subtitle** (12px, 60% opacity): Purpose text, truncated to 2 lines
- **Item count badge** (10px, accent background): Shows node count (e.g., "8 nodes")
- **Hover state**: Slight scale-up (1.03×), shadow depth increase, accent border widens to 6px

### 6.2 Overview Arrow Styling

- **Main spine arrows**: 2px solid, `#94a3b8` color, straight horizontal with arrowheads
- **Branch arrows**: 2px solid, slightly lighter, quadratic Bézier curves
- **Conditional arrows**: 2px dashed, with small condition label at midpoint
- **Flow dots**: 3px circles at 50% arrow color, 2–3 per arrow, traveling at 40px/sec
- **Hover highlight**: Arrow under cursor brightens to accent color of source block

### 6.3 Focus+Context Opacity Model

| Element | Focused Stage | Adjacent Stage | Distant Stage |
|---------|--------------|----------------|---------------|
| Lane background | 100% | 25% | 8% |
| Node fill | 100% | 20% | hidden |
| Node border | 100% | 15% | hidden |
| Node label | 100% | 30% (name only) | hidden |
| Edge | 100% | 15% | hidden |
| Edge label | 100% | hidden | hidden |

### 6.4 Breadcrumb Styling

- Horizontal bar, 32px height, below control bar, above canvas
- Background: `#f8fafc` (matching site header area)
- Segments separated by `›` chevron in `#94a3b8`
- Current segment: bold, accent color of focused stage
- Previous segments: normal weight, `#64748b`, underline on hover
- Transition: Segments slide in from right with 200ms ease-out

## 7. Data Model Changes

### 7.1 Summary Group Topology

Add an `edges` array to the summary groups data:

```javascript
var SUMMARY_TOPOLOGY = [
    { from: "acquire", to: "land", type: "required" },
    { from: "acquire", to: "parse", type: "required" },
    { from: "land", to: "validate", type: "required" },
    { from: "parse", to: "validate", type: "required" },
    { from: "validate", to: "warehouse", type: "conditional", label: "gates pass" },
    { from: "warehouse", to: "timeseries", type: "required" },
    { from: "warehouse", to: "serve", type: "required" },
    { from: "timeseries", to: "serve", type: "required", label: "enriched" },
    { from: "serve", to: "deploy", type: "required" }
];
```

### 7.2 Guided Mode Step Schema

Extend each guided mode step with zoom-level targeting:

```javascript
{
    targetZoom: "overview",      // "overview" | "subsystem" | "detail"
    targetGroup: "warehouse",    // summary group ID (for overview/subsystem)
    targetNode: "dim_occupation", // node ID (for detail level)
    text: "Step description...",
    lessonLink: "/lessons/2"     // optional
}
```

### 7.3 Block Layout Positions

Overview blocks use a directed-graph layout computed from `SUMMARY_TOPOLOGY`:

- Topological sort determines horizontal rank (x position)
- Blocks at the same rank are stacked vertically
- The layout algorithm respects a maximum of 3 blocks per rank
- Block centers are snapped to a 280×180 grid (220px block + 60px gap, 140px block + 40px gap)

## 8. Accessibility

All v2 changes maintain the v1 accessibility baseline:

- **Breadcrumb**: Uses `<nav aria-label="Breadcrumb">` with `<ol>` markup per WAI-ARIA breadcrumb pattern
- **Focus+context**: Dimmed elements remain in the accessibility tree; screen reader announces focused stage name
- **Subsystem view**: Node names in expanded blocks are announced via `aria-live` region
- **Zoom-aware guided modes**: Step transitions announce current zoom level and target name
- **Keyboard navigation**: All zoom levels fully keyboard-navigable (see Section 5.2)
- **Reduced motion**: All new animations (flow dots, breadcrumb transitions, block expansion) disabled when `prefers-reduced-motion: reduce` is active
- **Color contrast**: Focus+context opacity values chosen so focused elements exceed WCAG AA contrast ratios; dimmed elements are decorative context, not interactive targets

## 9. Performance Considerations

- **Subsystem rendering**: Expanded blocks with node-name boxes use simplified rendering (rectangles + text, no shape variants) to keep draw calls low
- **Focus+context**: Distant stages render only lane backgrounds (1 fillRect per lane), not individual nodes — lower cost than full rendering
- **Flow animation**: Uses a single `flowPhase` counter incremented per frame; dot positions computed arithmetically, no per-dot state objects
- **Bézier arrows**: Control points computed once at init (in `computeSummaryBlocks`) and cached; only the flow dots recompute position per frame
- **Canvas state**: Minimize `save()`/`restore()` calls by batching same-opacity draws together

## 10. File Impact Assessment

| File | Change Scope | Description |
|------|-------------|-------------|
| `pipeline_graph_data.js` | Moderate | Add `SUMMARY_TOPOLOGY` array, extend guided mode steps with `targetZoom` field |
| `pipeline.js` | Major | New layout engine, focus+context rendering, subsystem view mode, breadcrumb updates, revised guided mode engine, topology arrows |
| `pipeline.html` | Minor | Add breadcrumb `<nav>` element |
| `main.css` | Minor | Breadcrumb styles, subsystem-specific visibility rules |
| `test_pipeline.py` | Minor | New tests for breadcrumb, topology data, view modes |

## 11. Acceptance Criteria

The v2 iteration is complete when:

1. The default overview shows a **left-to-right pipeline flow** with branching topology — not a grid of cards.
2. Clicking a block **expands it** into a subsystem view showing node names, while **dimming** (not hiding) surrounding stages.
3. A **breadcrumb bar** shows the current navigation path and each segment is clickable.
4. Overview arrows show **branching, merging, and conditional** connections matching the real pipeline structure.
5. Overview arrows have **subtle flow animation** (moving dots) indicating data direction.
6. There are **three distinct zoom levels** (overview, subsystem, detail) with smooth transitions between them.
7. **Guided modes** start at the overview level and progressively zoom into relevant stages and nodes.
8. All new features respect **`prefers-reduced-motion`** and maintain WCAG AA accessibility.
9. All existing v1 functionality (search, filters, overlays, minimap, detail panel, keyboard navigation, URL hash) continues to work correctly.
10. All tests pass, lint is clean, and the static site builds successfully.

## 12. References

- `docs/specs/pipeline_explorer_design.md` — Original v1 design requirements (22 sections)
- `docs/specs/pipeline_explorer_plan.md` — V1 release plan (140/140 tasks complete)
- Section 5 of v1 spec: Core Interaction Model (overview+detail, focus+context, semantic zoom, breadcrumbs)
- Section 6 of v1 spec: Natural Zoom and Pan Design (four tiered zoom levels)
- Section 13 of v1 spec: Entertaining and Visually Engaging Elements (flow animation, micro-interactions)
- Microsoft Semantic Zoom guidance: zoomed-in and zoomed-out views should stay structurally consistent
- Shneiderman's Visual Information Seeking Mantra: overview first, zoom and filter, details on demand
