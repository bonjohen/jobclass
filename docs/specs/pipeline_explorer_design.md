# Pipeline Explorer Design Requirements

## 1. Purpose

JobClass already presents itself as a layered labor-market product with a warehouse, analyst marts, a reporting site, a methodology section, a lessons section, and time-series analysis pages. The repository README and live site show a four-layer warehouse, a top navigation with Home, Search, Hierarchy, Trends, Methodology, and Lessons, and an explicit educational goal around explaining the data, architecture, validation, and lessons learned. The new feature should extend that identity by adding a visual “Pipeline Explorer” that makes the system legible as a living graph rather than as static prose alone. ([GitHub][1])

This page should not be a decorative diagram. It should be an explorable model of how JobClass works: where data comes from, how it moves through Raw, Staging, Core, and Marts, how validation gates affect flow, how the web pages consume the results, and how special paths such as time-series refresh, CPI adjustment, SOC crosswalk, static generation, and deployment fit into the whole. The design should make the project easier to learn, easier to trust, and more fun to explore. The existing project already emphasizes lineage, validation, time-series comparability, and educational lessons; this page should visually unify those ideas. ([GitHub][1])

## 2. Product Intent

The Pipeline Explorer should serve four goals at once.

First, it should explain the end-to-end system to a new visitor in less than two minutes.

Second, it should let a technical reviewer drill into real project details such as node purpose, inputs, outputs, conditions, metadata, related lessons, and affected pages.

Third, it should make conditional behavior visible. Examples include SOC needing to load before dependent datasets, schema drift blocking publication, comparable-history versus as-published paths, and optional or release-specific branches such as CPI and crosswalk support. ([GitHub][2])

Fourth, it should be enjoyable to use. “Enjoyable” here means smooth navigation, satisfying transitions, a sense of discovery, and visible cause-and-effect. It should feel like a technical atlas or animated systems map, not like a corporate org chart.

## 3. Placement Within the Current Site

The new page should be a first-class part of the site, not hidden in Methodology.

Add a top-level navigation item called Pipeline. Place it between Trends and Methodology. This is the cleanest fit with the current navigation because the new page is more interactive than Methodology, more explanatory than Trends, and closely related to Lessons. The page should also have deep links from Methodology and from relevant lesson pages. The Lessons section was explicitly designed to help someone return to the project later and understand architecture, data quality traps, time-series behavior, and deployment limits; the Pipeline Explorer should act as the visual companion to that goal. ([bonjohen.github.io][3])

## 4. Experience Concept

The page should be designed as a “living pipeline atlas.”

At the highest level, the visitor sees a clean, full-width interactive graph that explains the project from source acquisition to visible website behavior. It should open centered and already fit to screen. The first impression should be clarity, not chaos.

The visual tone should match the current JobClass site: restrained, professional, text-forward, and information-dense. The novelty should come from motion, depth, interaction, and progressive disclosure, not from loud colors or game-like ornament. Current pages are simple and readable, so this new page should remain consistent with that baseline while becoming the most visually engaging part of the product. ([bonjohen.github.io][3])

A good mental model is “technical blueprint meets transit map meets explorable lesson.” It should feel alive through subtle flow animation and responsive zoom, but still read like a serious analytical product.

## 5. Core Interaction Model

The interaction model should follow the classic information-visualization pattern of overview first, zoom and filter, then details on demand. It should also combine overview+detail and focus+context so the visitor never loses their place while drilling deeper. Semantic zoom should be used rather than simple optical magnification, meaning that deeper zoom levels reveal different and richer representations rather than only larger shapes. ([Computer Science at UMD][4])

That translates into the following required behavior.

On first load, show the entire system at a comprehensible top level.

Allow pan and zoom immediately, with zoom anchored naturally to the pointer or gesture center.

Keep a minimap or overview inset visible so the user always knows where they are.

When the user zooms in, nodes should reveal new structure and not just enlarge.

When the user hovers, show a concise preview.

When the user selects, open a persistent properties panel.

When the user drills in, preserve context through breadcrumbs, highlighted ancestry, and a stable visual layout.

The user should never feel trapped in an infinite canvas with no orientation.

## 6. Natural Zoom and Pan Design

The zoom model should be semantic and tiered.

At the outermost level, the graph should show major lanes or grouped blocks only. These should include Sources, Extraction, Raw, Staging, Core Warehouse, Marts, API/Web, Validation/Observability, and Deployment/Static Output.

At the next level, each major block expands into subsystem nodes. For example, Sources expands into SOC, OEWS, O*NET, Employment Projections, CPI, and SOC Crosswalk. Core expands into dimensions, facts, bridges, and time-series structures. API/Web expands into search, hierarchy, trends, methodology, lessons, and the new pipeline page.

At the next level, a node opens into internal behaviors, interfaces, metadata, and conditional gates. A node should reveal things like input datasets, output tables or pages, CLI commands, validation rules, key lessons, and notable failure modes.

At the deepest level, the user should stop “zooming” and transition into a detail view. This can be a right-side properties drawer, an overlay panel, or a subpage view, but it should feel like a natural continuation of the graph rather than a separate product.

Pan and zoom must feel map-like. Mouse wheel or pinch zoom, click-drag pan, double-click to dive, and a clear reset-to-overview action should all be supported. The layout should resist disorientation by keeping group boundaries and major lanes stable across zoom levels. Microsoft’s semantic zoom guidance is useful here: zoomed-in and zoomed-out views should stay structurally consistent and predictable, not become different worlds. ([Microsoft Learn][5])

## 7. Top-Level Graph Structure

The default overview should present the project as a left-to-right or top-to-bottom flow with explicit grouped lanes.

A natural grouping is:

Sources

Acquisition and run manifest

Raw landing

Staging and parsing

Validation gates

Core warehouse

Time-series enrichment

Analyst marts

APIs and static generation

Website pages

Testing, health, readiness, metrics, and deployment

This structure matches the repository’s documented four-layer warehouse, phase-based buildout, live methodology content, CLI usage, and release notes for time-series, CPI, and crosswalk support. ([GitHub][1])

The graph should clearly communicate that this is not a pure linear pipeline. It is a directed graph with gates, side paths, optional branches, and publish conditions.

## 8. Node Types

Define node classes clearly and style them consistently.

Source nodes represent external data products. These include SOC, OEWS, O*NET, Employment Projections, CPI-U, and SOC Crosswalk. ([GitHub][1])

Process nodes represent actions such as download, parse, validate, normalize, derive, publish, or deploy.

Storage nodes represent durable artifacts such as Raw files, staging tables, core facts, bridges, marts, static JSON, or the warehouse database.

Gate nodes represent conditions. These include schema drift, referential integrity, comparability mode restrictions, publish gating, readiness checks, and health checks. ([GitHub][1])

Interface nodes represent things a person touches: CLI commands, APIs, pages, worked examples, lesson pages, and downloads.

Lesson nodes represent educational anchors. These are not part of the data path but should be linkable context. The existing Lessons section already covers the federal data landscape, four-layer architecture, multi-vintage issues, data quality traps, time-series normalization, idempotent pipeline design, static site generation, testing, schema drift, extraction patterns, derived metrics, and geography pitfalls. Those topics are ideal educational companions to nodes in the graph. ([bonjohen.github.io][6])

## 9. Edge Types

Edges should be semantically meaningful and visually distinct.

Required data-flow edges should be solid and direct.

Conditional edges should be dashed and carry short condition labels.

Blocked or failure edges should be shown in an alert style and only become prominent when the user enables failure or validation overlays.

Optional or release-specific edges should be visible but visually secondary.

Educational relationship edges can connect nodes to lessons or methodology content in a lighter style.

Derived-data edges should look different from source-flow edges. This matters because the methodology page already distinguishes base metrics, derived metrics, projections, and comparable-history logic, and the graph should reinforce that. ([bonjohen.github.io][7])

Edge conditions should never be hidden. If the graph is going to teach, it must show why a path is allowed, blocked, or special.

## 10. Required Content Inside Each Node

Every node must support a standard detail model, even if some fields are blank.

Each node should have a clear title and one-line purpose.

Each node should identify its type.

Each node should show upstream inputs and downstream outputs.

Each node should show what kind of artifact it handles: file, table, bridge, mart, page, API, lesson, validation result, or deployment artifact.

Each node should have a short “why it exists” paragraph.

Each node should expose key metadata such as source version, data grain, refresh cadence, or invariants where appropriate.

Each node should list related commands, endpoints, tables, pages, or lessons when relevant.

Each node should show the most important failure modes or caveats.

Each node should support a “jump to related content” action.

This detail model is important because the page is supposed to be educational, not just structural.

## 11. Required Detail Views

Selecting a node or edge should open a persistent properties panel.

The panel should support tabs or sections such as Overview, Logic, Data, Interfaces, Validation, Metadata, Lessons, and Failure Modes.

For a source node, emphasize what it provides, update cadence, role in the system, and downstream dependents.

For a process node, emphasize behavior, gating conditions, and produced artifacts.

For a storage node, emphasize schema/grain summary, lineage, and consumers.

For an interface node, emphasize how users or other components consume it.

For an edge, emphasize the meaning of the relationship and any conditions on traversal.

The panel should not feel like raw documentation pasted into a box. It should be curated, compact, and visually structured.

## 12. Educational Layer

The page should do more than document the pipeline. It should teach the pipeline.

Add a guided mode called Follow the Data. In this mode, the user can start at a source and watch the path into Raw, Staging, Core, Marts, APIs, and pages.

Add a guided mode called What Can Break. In this mode, the graph highlights schema drift, unmapped codes, suppressed values, comparability restrictions, and publish gates.

Add a guided mode called Time-Series Path. This mode highlights the time-series refresh path, CPI-backed real wages, crosswalk-related comparability, and the trend pages.

Add a guided mode called From Query to Proof. This mode starts from a visible page or metric and traces backward to marts, facts, and sources.

Each guided mode should be lightweight, skippable, and link to relevant lessons. This aligns well with the project’s existing educational material, which was intentionally written so a future reader could return months later and quickly understand the system. ([GitHub][2])

## 13. Entertaining and Visually Engaging Elements

The page should feel alive, but with restraint.

Use subtle animated pulses on active paths when a guided mode is running or when a node is selected. The animation should suggest flow, not simulate a video game.

Use soft layer glows or halos to show grouped zones such as Raw, Staging, Core, Marts, and Web.

Use small status chips on nodes to indicate source, derived, conditional, optional, blocked, or lesson-linked status.

Use tasteful micro-interactions such as edge brightening on hover, breadcrumb highlights, and smooth camera transitions on dive-in or reset.

Use a compact minimap that looks intentional, not like a developer tool.

Use transition choreography that makes the graph feel coherent. A user should feel like they are moving through one space.

Novelty should come from the way the graph reveals structure and causality. It should not come from visual noise.

## 14. Style Alignment Rules

The existing site is text-led, clean, and professional, with straightforward headings and simple navigation. The Pipeline Explorer should preserve that tone. ([bonjohen.github.io][3])

That means the base palette should remain restrained.

Typography should remain consistent with the rest of the site.

Color should carry meaning, not decoration.

Motion should be subtle and useful.

Panels and controls should feel like part of JobClass, not like a third-party embedded demo.

The graph itself can be visually richer than the rest of the site, but the surrounding shell should remain unmistakably JobClass.

## 15. Search, Filter, and Focus Tools

The page should include a graph-specific control bar.

Users should be able to search for a node by name, table, page, lesson, or concept.

Users should be able to filter by type such as source, validation, mart, page, lesson, or deployment.

Users should be able to filter by domain such as time-series, extraction, similarity, deployment, or lessons.

Users should be able to toggle overlays such as validation paths, failure paths, lesson links, or time-series branches.

Users should be able to isolate a path from selected node to visible page.

Users should be able to reset quickly to the full overview.

These tools should be lightweight and prominent. The graph will be much more useful if the user can trim complexity without leaving the page.

## 16. Integration With Existing Pages

The new page should integrate tightly with Methodology and Lessons.

Methodology should link into major lanes of the graph.

Lessons should link directly to nodes or subgraphs. For example, Lesson 1 should connect to the source group, Lesson 2 to the four-layer architecture, Lesson 5 to time-series nodes, Lesson 7 to static generation, Lesson 13 to schema drift, Lesson 16 to extraction, and Lesson 17 to derived metrics. ([bonjohen.github.io][6])

Occupation and trend pages should be able to deep-link into provenance paths inside the graph.

The graph should also expose reverse links back to the pages or lessons it helps explain.

## 17. Content Scope for Release 1

The first release should not attempt to expose every file or internal helper.

Release 1 should cover the main source systems, major pipeline stages, validation gates, time-series branch, main marts, major API surfaces, visible pages, static generation, deployment/health surfaces, and lesson anchors.

Release 1 should explicitly include the time-series path because the current project already documents and exposes time-series analysis, comparable history, derived metrics, real wage UI, and the `timeseries-refresh` pipeline command. ([bonjohen.github.io][7])

Release 1 should also explicitly include the educational branch because Lessons is already a first-class part of the site and repository. ([bonjohen.github.io][6])

## 18. Page Layout Requirements

The page should be divided into four stable zones.

A top navigation and compact page header consistent with the rest of the site.

A main graph canvas occupying most of the horizontal space.

A detail drawer or side panel for the selected node or edge.

A compact minimap and control cluster for zoom, filters, overlays, and reset.

On smaller screens, the graph should remain the primary surface, but the detail panel can become a bottom sheet or secondary overlay.

The default layout should still prioritize the graph. The graph is the product here.

## 19. Accessibility and Usability Requirements

The current project already emphasizes accessibility and responsive behavior. This page must continue that standard rather than becoming an exception. The project README and site content already reference accessibility work and tests, so the Pipeline Explorer must be keyboard-navigable, screen-reader-labeled at the control level, and usable with reduced-motion preferences. ([GitHub][1])

Required behaviors include keyboard traversal between major nodes, a keyboard-accessible way to open details, visible focus states, a reduced-motion mode, readable color contrast, and a non-pointer way to reset view and navigate breadcrumbs.

Even if the full graph cannot be narrated in a simple linear way, the controls, selected item state, and associated details must be accessible.

## 20. Content Sources the Coding Agent Should Use

The coding agent should mine the repository for graph content, not invent a fake system map.

The README should provide the main product story, sources, warehouse layers, CLI commands, release notes, and site structure. ([GitHub][1])

The live site should provide actual page names and user-facing concepts. ([bonjohen.github.io][3])

The lessons design and lessons list should provide educational anchors, terminology, and “why this matters” narratives. ([GitHub][2])

Schema and specs files should supply accurate table names, artifacts, and time-series terminology. ([GitHub][8])

The resulting page should reflect the real project, not a generalized ETL diagram.

## 21. Acceptance Criteria

The finished feature is only complete when it is visibly working in the application, not merely implemented in code.

The page must load with a comprehensible overview already fit to screen.

The user must be able to zoom, pan, reset, search, hover, and select.

The user must be able to drill from top-level lanes into deeper details without losing orientation.

The user must be able to open properties for both nodes and edges.

The user must be able to enter at least one guided educational mode and one failure-mode view.

The page must visibly connect to existing Methodology and Lessons content.

The page must work against the real project content model, not a hardcoded toy graph.

The deployed application must be opened and exercised through the actual website. A reviewer must verify the visible behavior directly, including hover behavior, selection behavior, zoom behavior, minimap behavior, breadcrumbs, filters, and at least one guided path.

For this feature, “working” means the user can actually explore the graph in the running site and learn something real from it.

## 22. Final Design Direction

Build this as a serious but delightful “Pipeline Explorer” that turns JobClass into its own explorable lesson.

The page should honor the project’s existing strengths: layered architecture, lineage, validation, time-series rigor, lessons-driven teaching, and a clean reporting aesthetic. It should add novelty through semantic zoom, focus+context navigation, animated path tracing, and rich details-on-demand. It should feel like the most memorable page in the site, while still looking unmistakably like JobClass.

[1]: https://github.com/bonjohen/jobclass "GitHub - bonjohen/jobclass: Labor market occupation data pipeline — ingests SOC, OEWS, O*NET, and BLS Projections into a layered analytical warehouse · GitHub"
[2]: https://github.com/bonjohen/jobclass/blob/main/docs/specs/lessons_design.md "jobclass/docs/specs/lessons_design.md at main · bonjohen/jobclass · GitHub"
[3]: https://bonjohen.github.io/jobclass/ "JobClass — Labor Market Reporting"
[4]: https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf "The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations - Visual Languages, 1996. Proceedings., IEEE Symposium on"
[5]: https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/semantic-zoom "Semantic zoom - Windows apps | Microsoft Learn"
[6]: https://bonjohen.github.io/jobclass/lessons "Lessons — JobClass"
[7]: https://bonjohen.github.io/jobclass/methodology "Methodology — JobClass"
[8]: https://github.com/bonjohen/jobclass/tree/main/docs "jobclass/docs at main · bonjohen/jobclass · GitHub"
