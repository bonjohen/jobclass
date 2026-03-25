# Phased Release Plan — CPI Domain Expansion

This document tracks the work required to elevate CPI from an internal wage deflator into a first-class analytical domain within JobClass, following the requirements in `cpi_expansion_design.md`.

The CPI domain parallels the existing occupation domain: browsable members, a formal BLS hierarchy, area availability, series variants, relative importance, average prices, and cross-cutting analytical relationships. BLS is the system of record; FRED and Cleveland Fed are optional overlays. The key design move is separating **member** from **series variant**, and separating the **formal hierarchy** from **cross-cutting analytical relationships**.

## Status Key

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Unprocessed — not yet started |
| `[>]` | Processing — work in progress |
| `[X]` | Complete — finished and verified |
| `[!]` | Paused — started but blocked or deferred |

## How To Use This Document.

Use this document as a work queue, managing the Status of each item according to the status key.

**Columns**: Status, Task ID, Description, Started, Completed

---

## Phase CPI0: Schema & Migrations

Create all dimension, bridge, fact, and staging tables for the CPI domain. This establishes the data model before any ingestion work begins.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI0-01 | Create migration: `dim_cpi_member` table (member_key, member_code, title, hierarchy_level, semantic_role [hierarchy_node / special_aggregate / average_price_item / purchasing_power / external_overlay], is_cross_cutting, has_average_price, has_relative_importance, publication_depth, source_version), sequence `seq_cpi_member_key`, unique index on (member_code, source_version) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-02 | Create migration: `bridge_cpi_member_hierarchy` table (parent_member_key, child_member_key, hierarchy_depth, source_version), foreign keys to `dim_cpi_member` | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-03 | Create migration: `bridge_cpi_member_relation` table (member_key_a, member_key_b, relation_type [core_aggregate / energy / commodities / services / purchasing_power / average_price_companion / cleveland_fed_overlay / fred_mirror], description, source_version), foreign keys to `dim_cpi_member` | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-04 | Create migration: `dim_cpi_area` table (area_key, area_code, area_title, area_type [national / region / division / size_class / cross_classification / metro], publication_frequency [monthly / bimonthly], source_version), sequence `seq_cpi_area_key`, unique index on (area_code, source_version) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-05 | Create migration: `bridge_cpi_area_hierarchy` table (parent_area_key, child_area_key, source_version), foreign keys to `dim_cpi_area` | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-06 | Create migration: `dim_cpi_series_variant` table (variant_key, series_id, index_family [CPI-U / CPI-W / C-CPI-U], seasonal_adjustment [S / U], periodicity [R / S], area_code, item_code, member_key, area_key, source_version), sequence `seq_cpi_variant_key`, unique index on (series_id, source_version) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-07 | Create migration: `fact_cpi_observation` table (member_key, area_key, variant_key, time_period_key, index_value, percent_change_month, percent_change_year, source_release_id, load_timestamp), grain: variant × period | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-08 | Create migration: `fact_cpi_relative_importance` table (member_key, area_key, reference_period, relative_importance_value, source_release_id, load_timestamp), grain: member × area × reference_period | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-09 | Create migration: `fact_cpi_average_price` table (member_key, area_key, time_period_key, average_price, unit_description, source_release_id, load_timestamp), grain: member × area × period | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-10 | Create migration: `fact_cpi_revision_vintage` table (member_key, area_key, time_period_key, vintage_label, index_value, is_preliminary, revision_date, source_release_id, load_timestamp), grain: member × area × period × vintage | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-11 | Create staging tables: `stage__bls__cpi_series`, `stage__bls__cpi_item_hierarchy`, `stage__bls__cpi_publication_level` | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI0-12 | Create staging tables: `stage__bls__cpi_relative_importance`, `stage__bls__cpi_average_price` | 2026-03-25 | 2026-03-25 |

---

## Phase CPI1: Manifest & Raw Capture

Add source manifest entries for all CPI data products and verify raw artifact capture with checksums.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI1-01 | Add manifest entry for CPI-U series data (BLS bulk download or API series pulls) in `source_manifest.yaml` | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI1-02 | Add manifest entry for CPI item aggregation tree file (BLS item structure/hierarchy) | 2026-03-25 | 2026-03-25 |
| `[!]` | CPI1-03 | Add manifest entry for CPI publication-level appendix (Appendix 7 — items by publication level). *Deferred: publication frequency is derived from area code patterns in the area parser instead of ingesting Appendix 7 as a separate data product.* | 2026-03-25 | |
| `[X]` | CPI1-04 | Add manifest entry for CPI relative importance tables (annual and monthly) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI1-05 | Add manifest entry for CPI average price tables (food, utility, motor fuel items) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI1-06 | Add manifest entry for CPI area definitions (area codes, types, hierarchy, publication frequency) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI1-07 | Ensure BLS browser-header download support works for CPI endpoints (reuse existing `Sec-Fetch-*` headers from download.py) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI1-08 | Verify raw capture: run extract for all CPI manifest entries, confirm immutable artifacts stored with file name, source URL, download timestamp, and checksum | 2026-03-25 | 2026-03-25 |

---

## Phase CPI2: Parsers

Implement dataset-specific parsers for each CPI data product. Each parser transforms raw BLS artifacts into staging-table-ready structures.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI2-01 | Implement CPI item hierarchy parser: parse BLS aggregation tree into member rows + parent-child hierarchy edges, classify hierarchy_level (All items / Major group / Intermediate aggregate / Expenditure class / Item stratum / ELI) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-02 | Implement CPI series metadata parser: decompose BLS series IDs into index_family, seasonal_adjustment, periodicity, area_code, item_code; validate each component against known member/area codes | 2026-03-25 | 2026-03-25 |
| `[!]` | CPI2-03 | Implement CPI publication-level parser: parse Appendix 7 into member × area_type availability matrix. *Deferred: publication frequency is classified by `_classify_publication_frequency()` in the area parser using area code patterns, not by parsing Appendix 7.* | 2026-03-25 | |
| `[X]` | CPI2-04 | Implement CPI area parser: parse area codes, titles, types (national, region, division, size class, cross-classification, metro), and publication frequency (monthly vs bimonthly) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-05 | Implement CPI series data parser: parse monthly index values into observation rows with period, value, and optional percent-change fields | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-06 | Implement CPI relative importance parser: parse annual/monthly relative importance tables into member × area × period rows | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-07 | Implement CPI average price parser: parse average price tables into member × area × period rows with unit descriptions | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-08 | Implement series ID decomposition validator: verify that encoded components in each series ID match known member codes and area codes; flag unresolved codes | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-09 | Add parser unit tests with representative BLS source files for each parser (hierarchy, series, publication level, area, observations, importance, average prices) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI2-10 | Add schema contract tests for all CPI staging tables: verify expected columns, types, and non-null constraints | 2026-03-25 | 2026-03-25 |

---

## Phase CPI3: Loaders & Pipeline Wiring

Load parsed CPI data into warehouse dimensions, bridges, and facts. Wire CPI into the pipeline orchestration.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI3-01 | Implement `load_dim_cpi_member()`: load member dimension from parsed item hierarchy, classify semantic_role for each member, set is_cross_cutting flag for special aggregates | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-02 | Implement `load_bridge_cpi_member_hierarchy()`: load formal tree edges from parsed hierarchy, validate tree consistency (no cycles, single root) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-03 | Implement `load_bridge_cpi_member_relation()`: load cross-cutting relationships (core CPI, energy, commodities, services, purchasing power) with explicit relation_type classification | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-04 | Implement `load_dim_cpi_area()`: load area dimension from parsed area definitions, set publication_frequency per area | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-05 | Implement `load_bridge_cpi_area_hierarchy()`: load area tree edges (national → region → division → metro) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-06 | Implement `load_dim_cpi_series_variant()`: load series variant dimension, link each variant to member_key and area_key via foreign key lookups | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-07 | Implement `load_fact_cpi_observation()`: load base index observations, join against dim_cpi_series_variant for variant_key resolution | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-08 | Create `cpi_refresh()` pipeline function in `pipelines.py`: orchestrate CPI extract → parse → validate → load sequence | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-09 | Add CPI to `run-all` orchestration: CPI is independent of OEWS/O\*NET, can run in parallel after taxonomy_refresh | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI3-10 | Add idempotent rerun test: run CPI pipeline twice, verify no duplicate rows in any CPI table | 2026-03-25 | 2026-03-25 |

---

## Phase CPI4: Core API Endpoints

Add resource-oriented API endpoints for CPI search, member detail, hierarchy navigation, series data, and area information.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI4-01 | Create `src/jobclass/web/cpi.py` API router with `/api/cpi/` prefix | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-02 | Add `/api/cpi/search` endpoint: search members by name or code, return matching members with title, code, hierarchy_level, and semantic_role | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-03 | Add `/api/cpi/members/{member_code}` endpoint: member detail with title, code, hierarchy position, semantic_role, available series variant count, ancestor chain, direct children count | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-04 | Add `/api/cpi/members/{member_code}/children` endpoint: list direct child members in hierarchy order | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-05 | Add `/api/cpi/members/{member_code}/relations` endpoint: list cross-cutting relationships with relation_type and related member details | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-06 | Add `/api/cpi/members/{member_code}/series` endpoint: time-series index values for the member, filterable by area_code, index_family, and seasonal_adjustment | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-07 | Add `/api/cpi/areas/{area_code}` endpoint: area detail with title, type, publication_frequency, published member count, area hierarchy position | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-08 | Add `/api/cpi/areas/{area_code}/members` endpoint: list members published in this area | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-09 | Define Pydantic response models for all CPI endpoints in `models.py` | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI4-10 | Add API unit tests: all CPI endpoints return 200 with expected fields for known members/areas | 2026-03-25 | 2026-03-25 |

---

## Phase CPI5: CPI Landing Page & Navigation

Add top-level CPI navigation, the landing page with headline series and member explorer entry, and CSS/JS scaffolding.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI5-01 | Add "CPI" nav link to `base.html` (placement: after Trends, alongside Pipeline/Methodology) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-02 | Add `/cpi` route to `app.py` returning `cpi.html` via `base.html` wrapper | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-03 | Create `cpi.html` landing page template: headline inflation series summary, member explorer entry cards, and short "How CPI is structured" explanation section | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-04 | Create `src/jobclass/web/static/js/cpi.js` with page initialization: load headline series, render summary cards | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-05 | Add CPI section CSS to `main.css`: member cards, hierarchy breadcrumbs, area badges, series charts | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-06 | Bump cache-busting version in `base.html` (`?v=CPI5`) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-07 | Add `/cpi` to `build_static.py` HTML page generation | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI5-08 | Verify: CPI landing page loads with real headline data and working navigation | 2026-03-25 | 2026-03-25 |

---

## Phase CPI6: CPI Member Page

Create the member detail page — the CPI equivalent of the occupation profile page — with hierarchy position, series values, variants, ancestors, descendants, siblings, and related aggregates.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI6-01 | Add `/cpi/member/{member_code}` route to `app.py` with 404 handling for unknown codes | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-02 | Create `cpi_member.html` template: title, member code, hierarchy level, semantic role, latest index value | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-03 | Implement ancestor chain display: breadcrumb-like hierarchy path from All Items → Major Group → ... → current member | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-04 | Implement descendant member list: direct children with their latest index values and relative importance (if available) | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-05 | Implement sibling comparison panel: all members at the same hierarchy level under the same parent | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-06 | Implement related special aggregates panel: cross-cutting relationships from `bridge_cpi_member_relation` with relation_type labels | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-07 | Implement time-series chart for member: monthly index values with year-over-year change overlay | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-08 | Implement series variant selector: list available variants (CPI-U, CPI-W, C-CPI-U, seasonally adjusted/not) and switch between them | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-09 | Implement area availability display: which areas publish this member, with publication frequency noted | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-10 | Add member pages to `build_static.py` per-member HTML and JSON generation | 2026-03-25 | 2026-03-25 |
| `[X]` | CPI6-11 | Verify: member page renders correctly for a hierarchy node (e.g., Housing) and a cross-cutting aggregate (e.g., All items less food and energy) | 2026-03-25 | 2026-03-25 |

---

## Phase CPI7: Relative Importance & Weighted Visualization

Add relative importance ingestion and the weighted hierarchy browser — the visually distinctive CPI explorer.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI7-01 | Implement `load_fact_cpi_relative_importance()`: load relative importance data from parsed tables, validate grain uniqueness | 2026-03-25 18:00 | 2026-03-25 18:02 |
| `[X]` | CPI7-02 | Add `/api/cpi/members/{member_code}/importance` endpoint: return relative importance history for the member | 2026-03-25 18:02 | 2026-03-25 18:06 |
| `[X]` | CPI7-03 | Add `/cpi/explorer` route to `app.py` | 2026-03-25 18:06 | 2026-03-25 18:07 |
| `[X]` | CPI7-04 | Create `cpi_explorer.html` template with canvas container for weighted hierarchy visualization | 2026-03-25 18:07 | 2026-03-25 18:09 |
| `[X]` | CPI7-05 | Create `cpi_explorer.js`: implement icicle/ribbon visualization where band widths represent latest relative importance values | 2026-03-25 18:09 | 2026-03-25 18:18 |
| `[X]` | CPI7-06 | Implement click-to-expand: clicking a band zooms into the next hierarchy layer while keeping parent context visible | 2026-03-25 18:09 | 2026-03-25 18:18 |
| `[X]` | CPI7-07 | Implement color mode switching: toggle between current monthly change, 12-month change, and contribution-to-headline views | 2026-03-25 18:09 | 2026-03-25 18:18 |
| `[X]` | CPI7-08 | Implement member lens side panel: on band selection, show compact member card with title, importance, change metrics, and link to full member page | 2026-03-25 18:09 | 2026-03-25 18:18 |
| `[X]` | CPI7-09 | Add relative importance history display on member page (below fold, CPI6 extension) | 2026-03-25 18:18 | 2026-03-25 18:22 |
| `[X]` | CPI7-10 | Add explorer page to `build_static.py` HTML and JSON generation | 2026-03-25 18:22 | 2026-03-25 18:28 |
| `[X]` | CPI7-11 | Verify: weighted visualization renders with real relative importance data, click-to-expand works, color modes switch correctly | 2026-03-25 18:28 | 2026-03-25 18:35 |

---

## Phase CPI8: Average Prices & Area Pages

Add average price ingestion, area detail pages, area hierarchy navigation, and the CPI comparison endpoint.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI8-00 | Review the test code and orchistration for performance issues. Implement any performance enhancements you think are important.| 2026-03-25 18:36 | 2026-03-25 18:52 |
| `[X]` | CPI8-01 | Implement `load_fact_cpi_average_price()`: load average prices from parsed tables, validate grain uniqueness, preserve unit descriptions | 2026-03-25 18:52 | 2026-03-25 18:55 |
| `[X]` | CPI8-02 | Add `/api/cpi/members/{member_code}/average-prices` endpoint: return average price history for applicable items (food, utility, motor fuel) | 2026-03-25 18:55 | 2026-03-25 18:58 |
| `[X]` | CPI8-03 | Add average price history section to `cpi_member.html` (visible only for members with has_average_price = true) | 2026-03-25 18:58 | 2026-03-25 19:02 |
| `[X]` | CPI8-04 | Add `/cpi/area/{area_code}` route to `app.py` with 404 handling | 2026-03-25 19:02 | 2026-03-25 19:08 |
| `[X]` | CPI8-05 | Create `cpi_area.html` template: area title, type, publication frequency, area hierarchy position, published item families, top inflationary members in latest period | 2026-03-25 19:02 | 2026-03-25 19:08 |
| `[X]` | CPI8-06 | Display area caveats prominently: "area indexes do not measure price-level differences among cities," volatility warning for local areas, bimonthly publication note where applicable | 2026-03-25 19:02 | 2026-03-25 19:08 |
| `[X]` | CPI8-07 | Handle bimonthly publication frequency: display gaps correctly in time-series charts, label bimonthly areas distinctly | 2026-03-25 19:02 | 2026-03-25 19:08 |
| `[X]` | CPI8-08 | Add `/api/cpi/compare` endpoint: compare time series across members or across areas, with alignment by period | 2026-03-25 19:08 | 2026-03-25 19:12 |
| `[X]` | CPI8-09 | Add area pages and compare endpoint to `build_static.py` HTML and JSON generation | 2026-03-25 19:12 | 2026-03-25 20:15 |
| `[X]` | CPI8-10 | Verify: area page shows correct publication rules and caveats; average price section appears only for applicable members | 2026-03-25 20:15 | 2026-03-25 20:25 |

---

## Phase CPI9: C-CPI-U Revision Vintage

Add support for C-CPI-U preliminary/revised values, which differ from final CPI-U and CPI-W data.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI9-01 | Implement `load_fact_cpi_revision_vintage()`: load C-CPI-U preliminary and revised values, track vintage_label and is_preliminary flag | 2026-03-25 20:28 | 2026-03-25 20:35 |
| `[X]` | CPI9-02 | Add revision vintage display on member page for C-CPI-U: show both preliminary and latest revised values side-by-side | 2026-03-25 20:35 | 2026-03-25 20:45 |
| `[X]` | CPI9-03 | Validate C-CPI-U constraints: national-only coverage, quarterly revision schedule | 2026-03-25 20:45 | 2026-03-25 20:48 |
| `[X]` | CPI9-04 | Mark preliminary values visually distinct from final values in all charts and tables (label + styling) | 2026-03-25 20:35 | 2026-03-25 20:45 |
| `[X]` | CPI9-05 | Add `/api/cpi/members/{member_code}/revisions` endpoint: return vintage comparison for C-CPI-U series | 2026-03-25 20:35 | 2026-03-25 20:45 |
| `[X]` | CPI9-06 | Add unit tests for revision vintage handling: verify preliminary/revised distinction, national-only constraint | 2026-03-25 20:48 | 2026-03-25 20:55 |

---

## Phase CPI10: Labor Domain Integration

Wire CPI and labor domains together with cross-domain panels, links, and methodology updates.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI10-01 | Add "price context" panel to occupation trend pages: display which CPI member drives the real-wage deflation, with link to CPI member page | 2026-03-25 20:58 | 2026-03-25 21:05 |
| `[X]` | CPI10-02 | Add "labor context" panel to CPI member pages: display which labor views (real-wage metrics) use this CPI family as a deflator | 2026-03-25 21:05 | 2026-03-25 21:08 |
| `[X]` | CPI10-03 | Link CPI deflator usage to existing `CPI_BASE_YEAR = 2023` constant and real-wage formula in time-series metrics | 2026-03-25 21:05 | 2026-03-25 21:08 |
| `[X]` | CPI10-04 | Show CPI base year, deflation formula, and source member on relevant occupation real-wage trend pages | 2026-03-25 20:58 | 2026-03-25 21:05 |
| `[X]` | CPI10-05 | Add cross-navigation links: CPI member pages → occupation real-wage views; occupation pages → CPI member pages | 2026-03-25 21:08 | 2026-03-25 21:10 |
| `[X]` | CPI10-06 | Update `methodology.html` with CPI domain documentation: data sources, hierarchy structure, area rules, revision behavior, real-wage integration | 2026-03-25 21:10 | 2026-03-25 21:15 |
| `[X]` | CPI10-07 | Verify: navigation between CPI and labor domains works bidirectionally with no dead ends | 2026-03-25 21:15 | 2026-03-25 21:18 |

---

## Phase CPI11: Community Overlays

Add optional FRED category mirrors and Cleveland Fed median/trimmed-mean inflation overlays. These are secondary to BLS data and visually distinct.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI11-01 | Add manifest entries for Cleveland Fed median CPI and 16% trimmed-mean CPI series | 2026-03-25 21:20 | 2026-03-25 21:22 |
| `[X]` | CPI11-02 | Implement Cleveland Fed parser: parse median and trimmed-mean inflation series into staging rows | 2026-03-25 21:22 | 2026-03-25 21:28 |
| `[X]` | CPI11-03 | Load Cleveland Fed data as overlay members in `dim_cpi_member` (semantic_role = external_overlay) with relation entries in `bridge_cpi_member_relation` | 2026-03-25 21:28 | 2026-03-25 21:35 |
| `[X]` | CPI11-04 | Implement FRED category mirror: map FRED CPI category structure to `bridge_cpi_member_relation` entries (relation_type = fred_mirror) | 2026-03-25 21:28 | 2026-03-25 21:35 |
| `[X]` | CPI11-05 | Add overlay toggle on CPI member pages and explorer: show/hide community data, clearly labeled as "External/Derived" | 2026-03-25 21:35 | 2026-03-25 21:40 |
| `[X]` | CPI11-06 | Style overlay data visually distinct from BLS base data: different badge color, "overlay" indicator, source attribution | 2026-03-25 21:35 | 2026-03-25 21:40 |
| `[X]` | CPI11-07 | Handle overlay data freshness independently: overlay refresh does not block BLS data pipeline | 2026-03-25 21:40 | 2026-03-25 21:42 |
| `[X]` | CPI11-08 | Verify: overlays visible but clearly secondary; toggling off overlays returns to pure BLS view | 2026-03-25 21:42 | 2026-03-25 21:45 |

---

## Phase CPI12: Tests, Static Build & Final Verification

Add automated tests for all CPI pages and endpoints, finalize static site integration, and verify end-to-end.

| Status | Task ID | Description | Started | Completed |
|--------|---------|-------------|---------|-----------|
| `[X]` | CPI12-01 | Create `tests/web/test_cpi.py` with test classes: `TestCPILanding`, `TestCPIMemberPage`, `TestCPIAreaPage`, `TestCPIExplorer`, `TestCPIAPI` | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-02 | Test: `/cpi` returns status 200 with correct page title and headline series content | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-03 | Test: `/cpi/member/{code}` returns 200 for a known hierarchy node and for a cross-cutting aggregate | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-04 | Test: `/cpi/area/{code}` returns 200 for U.S. city average and for a metro area | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-05 | Test: `/cpi/explorer` returns 200 with canvas/visualization container | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-06 | Test: `/api/cpi/search` returns results for known member names | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-07 | Test: all CPI API endpoints return expected JSON structure (member detail, children, relations, series, importance, average prices, revisions, areas, compare) | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-08 | Test: CPI nav link present on all pages | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-09 | Test: hierarchy navigation works — member page shows ancestor breadcrumbs and child list | 2026-03-25 21:48 | 2026-03-25 21:55 |
| `[X]` | CPI12-10 | Add all CPI pages and JSON endpoints to `build_static.py`: landing, member pages, area pages, explorer, search index, per-member JSON, per-area JSON | 2026-03-25 19:12 | 2026-03-25 20:15 |
| `[X]` | CPI12-11 | Run `ruff check src/ tests/` — all changed files pass linting | 2026-03-25 21:55 | 2026-03-25 21:58 |
| `[X]` | CPI12-12 | Run full test suite (`pytest`) — all existing + new CPI tests pass | 2026-03-25 21:55 | 2026-03-25 21:58 |
| `[X]` | CPI12-13 | Build static site and verify CPI pages render correctly at `/jobclass/cpi`, `/jobclass/cpi/member/{code}`, `/jobclass/cpi/area/{code}`, `/jobclass/cpi/explorer` | 2026-03-25 21:58 | 2026-03-25 22:05 |

---

## Phase Summary

| Phase | Description | Tasks | Status |
|-------|-------------|-------|--------|
| CPI0 | Schema & Migrations | 12 | **Complete** |
| CPI1 | Manifest & Raw Capture | 8 | 7/8 (1 deferred) |
| CPI2 | Parsers | 10 | 9/10 (1 deferred) |
| CPI3 | Loaders & Pipeline Wiring | 10 | **Complete** |
| CPI4 | Core API Endpoints | 10 | **Complete** |
| CPI5 | CPI Landing Page & Navigation | 8 | **Complete** |
| CPI6 | CPI Member Page | 11 | **Complete** |
| CPI7 | Relative Importance & Weighted Visualization | 11 | **Complete** |
| CPI8 | Average Prices & Area Pages | 11 | **Complete** |
| CPI9 | C-CPI-U Revision Vintage | 6 | **Complete** |
| CPI10 | Labor Domain Integration | 7 | **Complete** |
| CPI11 | Community Overlays | 8 | **Complete** |
| CPI12 | Tests, Static Build & Final Verification | 13 | **Complete** |
| **Total** | | **125** | |

---

## Notes

- **CPI0 must be done first.** All subsequent phases depend on the schema being in place.
- **CPI1 and CPI2 are sequential.** Raw capture must exist before parsers can process the artifacts.
- **CPI3 depends on CPI2.** Loaders consume parsed staging data.
- **CPI4 depends on CPI3.** API endpoints query loaded warehouse tables.
- **CPI5 and CPI6 depend on CPI4.** Pages consume API endpoints for data.
- **CPI7 depends on CPI3 (for importance data) and CPI6 (for member page extension).** The weighted explorer is the most visually distinctive feature and should ship once the base domain is stable.
- **CPI8 is independent of CPI7.** Average prices and area pages can be developed in parallel with the weighted explorer.
- **CPI9 can start after CPI3.** Revision vintage loading is independent of the web layer but should ship after CPI6 so the member page can display revisions.
- **CPI10 depends on CPI6.** Cross-domain links require both CPI and labor pages to exist.
- **CPI11 is intentionally last before testing.** Community overlays are secondary to BLS-first data and should not block the core domain.
- **CPI12 depends on all prior phases.** Final integration gate.
- **Incremental deployment is encouraged.** After CPI5, the landing page is usable. After CPI6, individual members are browsable. After CPI7, the explorer is visually engaging. Each milestone can be committed and deployed independently.
- **BLS is the system of record.** FRED and Cleveland Fed data are overlays, not canonical. They are visually distinguished and independently refreshable.
- **One member, many series variants.** A member like "Shelter" can have multiple series by index family (CPI-U/W/C), seasonal adjustment, area, and periodicity. The variant dimension encodes all of these.
- **Publication rules vary by area and member.** Not every item is published in every area class. Bimonthly metro areas have natural gaps. The UI must surface these rules, not hide them.
- **C-CPI-U is preliminary and revised.** CPI-U and CPI-W are final on release. C-CPI-U undergoes three quarterly revisions. The vintage fact handles this correctly.

## Critical Files

| File | Action | Phase |
|------|--------|-------|
| `src/jobclass/load/cpi.py` | New — CPI loaders | CPI3 |
| `src/jobclass/parse/cpi.py` | New — CPI parsers | CPI2 |
| `src/jobclass/extract/source_manifest.yaml` | Add CPI manifest entries | CPI1 |
| `src/jobclass/pipeline/pipelines.py` | Add `cpi_refresh()`, wire into `run-all` | CPI3 |
| `src/jobclass/web/cpi.py` | New — CPI API router | CPI4 |
| `src/jobclass/web/models.py` | Add CPI Pydantic response models | CPI4 |
| `src/jobclass/web/app.py` | Add CPI page routes | CPI5, CPI6, CPI7, CPI8 |
| `src/jobclass/web/templates/cpi.html` | New — CPI landing page | CPI5 |
| `src/jobclass/web/templates/cpi_member.html` | New — CPI member page | CPI6 |
| `src/jobclass/web/templates/cpi_area.html` | New — CPI area page | CPI8 |
| `src/jobclass/web/templates/cpi_explorer.html` | New — weighted hierarchy explorer | CPI7 |
| `src/jobclass/web/templates/base.html` | Add CPI nav link, bump cache version | CPI5 |
| `src/jobclass/web/static/js/cpi.js` | New — CPI page JS | CPI5 |
| `src/jobclass/web/static/js/cpi_explorer.js` | New — weighted visualization JS | CPI7 |
| `src/jobclass/web/static/css/main.css` | Add CPI CSS section | CPI5 |
| `src/jobclass/web/templates/methodology.html` | Add CPI methodology content | CPI10 |
| `scripts/build_static.py` | Add CPI page and JSON generation | CPI5–CPI12 |
| `tests/web/test_cpi.py` | New — CPI test suite | CPI12 |
