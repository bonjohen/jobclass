# Plan: Pipeline Explorer Release Plan Document

## Context
The user provided `docs/specs/pipeline_explorer_design.md` — a detailed design for an interactive graph-based Pipeline Explorer page. I need to generate a phased release plan document following the project's established convention (status key table, phase tables with `[ ]` checkboxes, task IDs, description columns).

## Action
Write `docs/specs/pipeline_explorer_release_plan.md` containing 14 phases (PE0–PE13), ~129 tasks total, following the exact format of `new_data_source_plan.md` and `lessons_release_plan.md`.

## Key Design Decisions
1. **Canvas-based rendering** (not SVG/DOM) — best perf for 100+ nodes with animation
2. **Static JS data model** — no API needed, works on GitHub Pages identically
3. **No third-party libraries** — consistent with project's vanilla-JS approach
4. **Full-width layout override** — canvas needs entire viewport width
5. **Guided modes are data-driven** — sequences defined in data file, not hardcoded in renderer
6. **Lesson mapping is explicit** — 20 lessons mapped to specific graph node IDs

## Critical Files
- `src/jobclass/web/app.py` — add `/pipeline` route
- `src/jobclass/web/templates/pipeline.html` — new template
- `src/jobclass/web/static/js/pipeline.js` — rendering engine (new)
- `src/jobclass/web/static/js/pipeline_graph_data.js` — graph data model (new)
- `src/jobclass/web/static/css/main.css` — Pipeline Explorer CSS section
- `src/jobclass/web/templates/base.html` — nav link + cache bust
- `scripts/build_static.py` — static site integration
- `tests/web/test_pipeline.py` — test suite (new)
- Multiple lesson templates + methodology.html — cross-link additions

## Verification
- Run `pytest tests/web/` after PE12
- Run `ruff check src/ tests/` after PE13
- Build static site and verify at localhost
- Verify on live server: graph renders, pan/zoom, node selection, guided modes, search, minimap, cross-links
