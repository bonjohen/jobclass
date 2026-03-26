# Pipeline Explorer Mockup Plan

Visual mockups of the Pipeline Explorer's summary topology and all 7 drill-in stage views. Each mockup is a self-contained HTML file with inline SVG, openable in any browser.

All node data, edge connections, and metadata are sourced from `src/jobclass/web/static/js/pipeline_graph_data.js`.

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

## Mockups

| Status | Task ID | File | Description | Nodes | Started | Completed |
|--------|---------|------|-------------|-------|---------|-----------|
| `[X]` | MK-00 | `00_summary_topology.html` | Top-level pipeline flow: 8 summary blocks with branching topology arrows | 8 blocks | 2026-03-26 14:30 PST | 2026-03-26 14:35 PST |
| `[X]` | MK-01 | `01_data_sources.html` | Data Sources stage: 6 federal sources, download manager, run manifest, browser-header workaround | 9 | 2026-03-26 14:40 PST | 2026-03-26 14:48 PST |
| `[X]` | MK-02 | `02_raw_landing.html` | Raw Landing stage: 6 immutable file storage nodes with path patterns and checksums | 6 | 2026-03-26 14:48 PST | 2026-03-26 14:53 PST |
| `[X]` | MK-03 | `03_stage_parse.html` | Stage & Parse: 7 dataset-specific parsers (SOC, OEWS, O\*NET, Projections, CPI, CPI Domain, Crosswalk) | 7 | 2026-03-26 14:48 PST | 2026-03-26 14:53 PST |
| `[X]` | MK-04 | `04_validation_gates.html` | Validation Gates: 6 sequential quality gates with pass/block conditions | 6 | 2026-03-26 14:53 PST | 2026-03-26 14:58 PST |
| `[X]` | MK-05 | `05_core_warehouse.html` | Core Warehouse: dims, facts, bridges, CPI dimensions, crosswalk mappings | 8 | 2026-03-26 14:53 PST | 2026-03-26 14:58 PST |
| `[X]` | MK-06 | `06_time_series.html` | Time-Series Enrichment: metric catalog, multi-vintage loading, CPI deflation, derived series, comparable history | 6 | 2026-03-26 14:53 PST | 2026-03-26 14:58 PST |
| `[X]` | MK-07 | `07_marts_web.html` | Marts & Web: 7 mart tables + 12 interface pages showing mart-to-page data flow | 19 | 2026-03-26 14:58 PST | 2026-03-26 15:05 PST |

---

## Visual Conventions

- **Dark background** (`#0f172a`) matching the summary topology mockup
- **Node shapes by type**: hexagons (source), rounded rectangles (process), cylinders (storage), diamonds (gate), pill shapes (interface)
- **Accent colors**: each stage uses its summary group accent color from `SUMMARY_GROUPS`
- **Edge styles**: solid (required), dashed (conditional), red dashed (blocked), dotted (optional), light (educational)
- **External connections**: ghost arrows at left/right edges showing incoming/outgoing connections to adjacent stages
- **Condition labels**: shown on edges where conditions are defined in `GRAPH_EDGES`

## Notes

- All mockups are static HTML+SVG with no JavaScript dependencies
- Node positions approximate the world-coordinate layout from `pipeline_graph_data.js`
- Mockups serve as design references for the PEv2 subsystem zoom level (Phase PEv2-5)
