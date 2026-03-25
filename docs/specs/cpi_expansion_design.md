# CPI Domain Expansion — Detailed Design Proposal

## 1. Goal

Extend JobClass so CPI becomes a first-class analytical domain, not just a supporting deflator for real wages. The codebase already treats CPI-U as an input to time-series real wage metrics, and the project already has a four-layer warehouse, time-series observation model, derived-series model, FastAPI site, and static-site deployment path. This extension should reuse those conventions and turn CPI into a browsable, nested, user-facing domain with its own hierarchy, member pages, comparisons, and methodology surfaces. ([GitHub][1])

## 2. Why CPI Fits the Existing Product

JobClass already organizes occupations as a backbone plus nested relationships, derived metrics, geography, and visible explanatory pages. CPI is a natural parallel domain because BLS publishes it as a structured hierarchy of items and areas, with formal series codes, weights, publication levels, and revisions. The repo also already documents CPI integration, real-wage UI support, and time-series refresh logic, so the next step is to elevate CPI from “used internally for wage deflation” to “explorable in its own right.” ([GitHub][1])

## 3. Research Summary

The relevant federal structure is strong enough to support a rich CPI explorer. BLS publishes CPI as monthly series, including CPI-U, CPI-W, C-CPI-U, and average prices. It also documents a formal item hierarchy, a series-ID structure, annual relative-importance data, publication-level availability by area type, local-area limitations, and the fact that C-CPI-U is national-only and revised quarterly. BLS additionally publishes appendices for entry-level items, publication levels, and average-price item lists. ([Bureau of Labor Statistics][2])

The current BLS item structure is especially useful for this feature because it is explicitly hierarchical. BLS describes the item classification as All items, Major groups, Intermediate aggregates, Expenditure classes, Item strata, and Entry level items. BLS also states that current CPI aggregation is built from 243 basic items in 32 basic areas, with 211 public item strata and 70 expenditure classes; not-seasonally-adjusted aggregate series are built bottom-up from basics, while seasonally adjusted aggregate series are not necessarily simple bottom-up sums. ([Bureau of Labor Statistics][3])

Community-facing CPI tools suggest two complementary patterns. FRED emphasizes browsing CPI and related inflation series by category and family, while the Cleveland Fed emphasizes derived “underlying inflation” views such as Median CPI and the 16 percent trimmed-mean CPI built from BLS component data. JobClass can combine those patterns: a BLS-first hierarchy browser plus optional analytical overlays for robust-summary inflation measures. ([FRED][4])

## 4. Product Outcome

The product should let a user navigate CPI the way they navigate occupations: from broad categories down to detailed members, with every member having visible relationships, a time series, area availability, methodological notes, and related derived measures. The user should be able to start from “All items,” “Housing,” “Shelter,” “Rent of primary residence,” “Energy,” or “Core CPI,” and move through the system without needing to know a BLS series code in advance. This should feel native to JobClass rather than like a bolted-on inflation calculator.

The most important design decision is to separate the **primary CPI tree** from **cross-cutting CPI aggregates**. The primary tree is the formal BLS hierarchy. Cross-cutting aggregates include series such as “all items less food and energy,” “services less energy services,” “energy,” and “purchasing power of the consumer dollar,” which are analytically important but not clean parent-child nodes in a single tree. The UI and data model should support both. That distinction is necessary because BLS publishes both hierarchical item structures and special indexes that cut across the hierarchy. ([Bureau of Labor Statistics][3])

## 5. Scope Boundary

The first implementation should stay BLS-first and monthly. It should support CPI-U, CPI-W, C-CPI-U, and average-price data where published. It should support the formal item hierarchy, area hierarchy, relative importance, and average-price items. It should expose local-area availability rules and C-CPI-U revision behavior. It should not begin by trying to absorb every inflation-related series from every outside source. ([Bureau of Labor Statistics][2])

Community and other-data integrations should be treated as overlays, not as the canonical store. FRED is useful for familiar category browsing and optional series mirrors, and the Cleveland Fed is useful for median and trimmed-mean overlays, but BLS should remain the system of record for CPI structure, primary series, and methodology. ([FRED][4])

## 6. Guiding Principles

This feature should inherit the repository’s existing conventions: immutable raw capture, idempotent loading, fail-fast schema drift detection, separation of observed versus derived metrics, and separation of as-published versus comparable history. The existing spec language for new data sources is still the right pattern: new sources attach to the established analytical architecture and should be independently deployable wherever practical. ([GitHub][5])

A new principle should be added for CPI: **one conceptual member, many possible series**. In CPI, “Shelter” is not a single line of data. It can have multiple series variants by index family, seasonal adjustment, area, and publication schedule. The domain model should therefore distinguish a **member** from a **series instance**. That is the key to making CPI feel navigable instead of cryptic.

## 7. Recommended Domain Model

The cleanest model is to introduce a CPI domain parallel to the occupation domain.

`dim_cpi_member` should represent item-like things a user can browse. This includes formal hierarchy nodes such as All items, Housing, Shelter, Rent of primary residence, and item strata or entry-level items when available. It should also include special aggregates, but those should be flagged as cross-cutting rather than purely hierarchical.

`bridge_cpi_member_hierarchy` should store the formal tree: all items to major group, major group to intermediate aggregate, intermediate aggregate to expenditure class, expenditure class to item stratum, and item stratum to ELI where the source data supports it. The member tree should be stable and navigable.

`bridge_cpi_member_relation` should store non-tree relationships. This is where “core CPI,” “energy,” “commodities,” “services,” “purchasing power,” “average price companion,” “Cleveland Fed derived overlay,” or “FRED mirror” belong. This table is important because CPI has meaningful analytical relationships that are not well represented as strict parent-child edges.

`dim_cpi_area` should represent U.S. city average, regions, divisions, size classes, region-size cross-classifications, and selected local areas. `bridge_cpi_area_hierarchy` should model the area tree where appropriate. BLS publishes indexes at different area levels and warns that local indexes are more volatile and are not measures of price-level differences across cities, so area metadata needs to be first-class. ([Bureau of Labor Statistics][6])

`dim_cpi_series_variant` should encode index family, seasonal adjustment, periodicity, publication schedule, area code, item code, and source system. This is justified by the BLS CPI series ID format, which explicitly encodes index type, seasonal adjustment status, periodicity, area code, and item code. ([Bureau of Labor Statistics][7])

## 8. Core Facts

`fact_cpi_observation` should become the base fact for CPI index observations. Its grain should be member, area, index family, adjustment status, periodicity, period, source release, and series identifier. This stores the published index itself and any directly published percent-change fields if you decide to persist them rather than compute them on read.

`fact_cpi_relative_importance` should store annual and monthly relative-importance observations separately from the base index series. Relative importance is not just another flavor of the index. It is an expenditure-share or value-weight measure, published on a distinct cadence and with explicit interpretive caveats from BLS. ([Bureau of Labor Statistics][8])

`fact_cpi_average_price` should store published average prices for the limited set of food, utility, and motor-fuel items BLS publishes. Average prices are price-level estimates, not index values, and BLS explicitly says they serve a different purpose from CPI indexes. They belong in a separate fact. ([Bureau of Labor Statistics][9])

`fact_cpi_revision_vintage` should store preliminary and revised C-CPI-U values where applicable. BLS states that CPI-U and CPI-W are final when released, while C-CPI-U is preliminary and subject to three subsequent quarterly revisions. A revision fact or vintage-aware extension is therefore necessary if C-CPI-U is to be treated correctly. ([Bureau of Labor Statistics][10])

## 9. Staging and Raw Additions

The raw layer should capture more than just a single CPI series pull. It should capture the BLS API series pulls, the item aggregation tree file, publication-level appendix data, relative-importance tables, and average-price tables. The CPI item aggregation tree and Appendix 7 publication-level data are essential if the site is going to let users browse members and understand where a member is published. ([Bureau of Labor Statistics][11])

The staging layer should therefore add at least these datasets: `stage__bls__cpi_series`, `stage__bls__cpi_item_hierarchy`, `stage__bls__cpi_publication_level`, `stage__bls__cpi_relative_importance`, and `stage__bls__cpi_average_price`. The existing repo conventions already use `stage__source__dataset` naming, so this fits the current style. ([GitHub][12])

## 10. Member Semantics

Each `dim_cpi_member` row should carry a clear semantic role. At minimum it should know whether it is a hierarchy node, a special aggregate, an average-price item, a purchasing-power item, or an external overlay. It should also know its publication depth, whether it is complete and mutually exclusive within the primary tree, whether it is cross-cutting, whether it is publishable at metro level, and whether it has average-price or relative-importance support.

This matters because BLS data availability varies by area and by member, and because special aggregates do not behave like strict tree nodes. BLS Appendix 7 exists specifically to show which items are published at which geographic levels, and BLS average prices are published only for selected items. ([Bureau of Labor Statistics][13])

## 11. Derived and Community Layers

The first release should keep derived CPI metrics modest: month-over-month change, year-over-year change, cumulative change over a selected period, purchasing-power inversion, and contribution-style views where the source data supports them. These derived measures should be clearly labeled as derived and should not replace the raw published indexes.

A second layer should support optional overlays from outside BLS. The best candidates are FRED category mirrors and Cleveland Fed median/trimmed-mean inflation series. FRED adds familiar browsing and user expectations around category grouping, while Cleveland Fed adds “underlying inflation” views that many serious users expect when exploring CPI beyond headline and core. These should be visible as overlays or related panels, not mixed into the base BLS member hierarchy. ([FRED][4])

## 12. Website Information Architecture

Add a top-level `CPI` section to the site. This should be parallel to Search, Hierarchy, Trends, Methodology, and Lessons, not buried inside the labor pages.

The CPI landing page should present the domain in three ways at once: headline inflation series, the item/member explorer, and a short explanation of how CPI is structured. The page should make it obvious that users can browse by category, compare areas, inspect weights, view average prices, and relate CPI back to labor metrics.

The primary explorer page should be a **weighted hierarchy browser**. The most natural visual is an icicle-style or ribbon-style hierarchy where horizontal width represents the latest relative importance and color represents current inflation pressure or change. This is a better fit than a plain tree because CPI is not only hierarchical; it is weighted. BLS publishes relative-importance data expressly for expenditure-share interpretation, so a weighted visual is meaningful rather than decorative. ([Bureau of Labor Statistics][8])

## 13. CPI Member Page

Every CPI member should have its own detail page, just as occupations do. That page should show the member title, code, hierarchy position, latest series values, available series variants, ancestor chain, descendant members, sibling comparison, and related special aggregates.

Below the fold, the member page should show a time series, area availability, relative importance history where available, average price history where applicable, and explanatory notes. For something like “Shelter,” the page should show descendants such as rent and owners’ equivalent rent, plus cross-cutting relations to all-items and core-like aggregates. For something like “Regular unleaded gasoline,” the page should also expose average price support if it exists. BLS publishes both hierarchy structure and average-price data for selected fuels and food items, which makes that combined page valuable. ([Bureau of Labor Statistics][11])

## 14. Area and Publication Views

CPI needs an area page as much as it needs a member page. The area page should show which item families are published there, whether the area is monthly or bimonthly, how that area sits in the area hierarchy, and which members are most inflationary in the latest period.

This is important because BLS area data has caveats that users often misunderstand. BLS says area indexes do not measure price-level differences among cities, many metro areas are published only every other month, and local indexes are more volatile because they are byproducts of the national CPI program with smaller samples. Those caveats should be visible in the UI, not hidden in documentation. ([Bureau of Labor Statistics][14])

## 15. Relationship Model in the UI

The UI should intentionally support two relationship modes.

The first mode is **Tree mode**, where users browse the formal BLS hierarchy.

The second mode is **Related mode**, where users see analytical neighbors and cross-cuts. This is where “all items less food and energy,” “services less energy services,” “energy,” “purchasing power of the consumer dollar,” median CPI, trimmed-mean CPI, or “related labor deflator uses” belong.

This dual model is necessary because CPI is not only a hierarchy. It is a hierarchy plus a set of heavily used analytical cuts and derived summaries.

## 16. Novel but Aligned Visual Suggestions

The JobClass site is already clean and professional, so the CPI section should stay restrained. The novelty should come from how structure and time are revealed.

The strongest visual suggestion is a **weighted inflation ribbon**. At the top level, it shows major CPI groups as bands whose widths reflect current relative importance. Clicking a band expands it into the next hierarchy layer while keeping the rest of the context visible. The color layer can switch between current monthly change, 12-month change, or contribution pressure. This is visually engaging, educational, and faithful to CPI’s weighted structure.

A second strong element is a **member lens**. When the user selects a node, a side panel opens with a compact “member card,” time series, variants, areas, weight history, and related aggregates. This keeps the page aligned with the rest of the site’s sober styling while making exploration satisfying.

## 17. API Surface

The API should remain resource-oriented.

At minimum, add endpoints for CPI search, CPI member detail, member children, member relations, member series variants, member time series, area detail, area members, relative importance, average prices, and CPI compare.

Representative endpoints would be `/api/cpi/members/{member_code}`, `/api/cpi/members/{member_code}/children`, `/api/cpi/members/{member_code}/relations`, `/api/cpi/members/{member_code}/series`, `/api/cpi/members/{member_code}/importance`, `/api/cpi/members/{member_code}/average-prices`, `/api/cpi/areas/{area_code}`, and `/api/cpi/compare`.

These should mirror the existing repo style, where the site consumes stable JSON resources rather than ad hoc query payloads. ([GitHub][1])

## 18. Labor Integration

The CPI domain should not remain isolated from the labor domain. The most valuable bridge is a “labor context” panel on CPI pages and a “price context” panel on labor pages.

On CPI pages, this can answer questions like which labor views currently use this CPI family or deflator. On labor pages, this can answer which CPI member is driving a real-wage adjustment or whether a real wage is being deflated by headline CPI or some future configurable alternative.

This keeps CPI relevant to JobClass’s core labor identity and prevents the CPI section from feeling like a detached annex.

## 19. Validation and Edge Cases

The new domain introduces specific validation requirements.

The parser must validate series-ID decomposition and member-code mapping, because the series ID encodes family, seasonal adjustment, periodicity, area, and item code. ([Bureau of Labor Statistics][7])

The warehouse must validate that member hierarchy edges form a consistent tree where expected, while allowing non-tree relations in the relation bridge.

The pipeline must validate publication-level rules, because not every item is published in every area class. ([Bureau of Labor Statistics][13])

The time-series layer must handle bimonthly local data correctly and explicitly represent missing October 2025 values rather than backfilling them invisibly. BLS has documented both the bimonthly publication pattern for many metro areas and the 2025 shutdown-related gap. ([Bureau of Labor Statistics][15])

C-CPI-U must be versioned or vintage-aware because preliminary and revised values differ by design. ([Bureau of Labor Statistics][10])

## 20. Phased Implementation

Phase 1 should make CPI structurally first-class. Add member, hierarchy, area, and base observation models; ingest the item hierarchy, publication levels, and expanded CPI series metadata; and expose a basic CPI landing page, member pages, and search.

Phase 2 should add relative importance and weighted visualization. This is the point where the explorer becomes visually distinctive.

Phase 3 should add average prices and area nuance. This adds a second kind of CPI fact and makes fuel/food/utility exploration much richer. BLS average prices are limited and different in meaning from indexes, so this is best done after the base index domain is stable. ([Bureau of Labor Statistics][9])

Phase 4 should add community overlays such as FRED mirrors and Cleveland Fed median/trimmed-mean inflation views. These are analytically valuable, but secondary to getting the BLS-first domain correct. ([FRED][4])

## 21. Acceptance Criteria

This feature is only complete when it works on real local data and in the visible application.

The CPI extract step must run locally and persist source artifacts.

The CPI hierarchy, publication-level, importance, and average-price datasets must load into the warehouse.

The CPI landing page, member page, area page, and compare page must open in the running site and render representative real data.

A reviewer must be able to navigate from All items to a major group, from that major group to a child member, from that member to a time series, and from that series to area or relation views without hitting a dead end.

The UI must visibly distinguish hierarchy nodes, special aggregates, average-price items, and external overlays.

## 22. Final Recommendation

Build CPI as a full analytical domain with its own members, hierarchies, areas, and facts, while keeping BLS as the canonical structure and treating FRED/Cleveland Fed as optional overlays. The crucial design move is to separate **member** from **series variant**, and to separate the **formal hierarchy** from **cross-cutting analytical relationships**.

That gives JobClass a CPI section that matches the richness of its occupation section: nested, explainable, browsable, time-aware, and genuinely useful instead of merely supportive.

[1]: https://github.com/bonjohen/jobclass "GitHub - bonjohen/jobclass: Labor market occupation data pipeline — ingests SOC, OEWS, O*NET, and BLS Projections into a layered analytical warehouse · GitHub"
[2]: https://www.bls.gov/opub/hom/cpi/presentation.htm "Presentation : Handbook of Methods: U.S. Bureau of Labor Statistics"
[3]: https://www.bls.gov/cpi/additional-resources/revision-1998-item-structure.htm "Changing the item structure of the Consumer Price Index :  U.S. Bureau of Labor Statistics"
[4]: https://fred.stlouisfed.org/categories/9 "Consumer Price Indexes (CPI and PCE) | FRED | St. Louis Fed"
[5]: https://github.com/bonjohen/jobclass/blob/main/docs/specs/new_data_source_design.md "jobclass/docs/specs/new_data_source_design.md at main · bonjohen/jobclass · GitHub"
[6]: https://www.bls.gov/cpi/overview.htm?utm_source=chatgpt.com "Consumer Price Indexes Overview"
[7]: https://www.bls.gov/cpi/factsheets/cpi-series-ids.htm "CPI series ID codes :  U.S. Bureau of Labor Statistics"
[8]: https://www.bls.gov/cpi/tables/relative-importance/ "Relative Importance and Weight Information for the Consumer Price Indexes :  U.S. Bureau of Labor Statistics"
[9]: https://www.bls.gov/cpi/factsheets/average-prices.htm "CPI: Average Price Data :  U.S. Bureau of Labor Statistics"
[10]: https://www.bls.gov/cpi/technical-notes/ "CPI News Release Technical Note :  U.S. Bureau of Labor Statistics"
[11]: https://www.bls.gov/cpi/additional-resources/cpi-item-aggregation.htm "CPI item aggregation :  U.S. Bureau of Labor Statistics"
[12]: https://github.com/bonjohen/jobclass/blob/main/docs/schema.md "jobclass/docs/schema.md at main · bonjohen/jobclass · GitHub"
[13]: https://www.bls.gov/cpi/additional-resources/index-publication-level.htm "CPI Handbook of Methods Appendix 7: CPI Items by Publication Level :  U.S. Bureau of Labor Statistics"
[14]: https://www.bls.gov/news.release/cpi.htm " Consumer Price Index News Release - 2026 M02 Results "
[15]: https://www.bls.gov/cpi/factsheets/approximating-missing-data.htm "Approximating missing data points :  U.S. Bureau of Labor Statistics"
