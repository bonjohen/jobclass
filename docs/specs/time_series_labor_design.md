# Time-Series Labor Intelligence Requirements

## 1. Goal

Extend the current JobClass system from point-in-time occupation reporting into a time-series labor intelligence system.

The new phase must preserve the current occupation-centered warehouse and reporting model, but add explicit support for observations over time, derived trend metrics, and visible analytical workflows for comparing occupations and geographies across time.

## 2. Core Product Requirement

The system must support analysis of occupation metrics over time, not just static profiles.

The system must treat occupation as the stable backbone and add time-indexed observations around it.

The system must support both raw published history and comparable trend history as separate analytical modes.

The system must expose these distinctions clearly in both data products and visible user-facing pages.

## 3. Data Model Requirements

Add a conformed metric catalog that defines each metric’s meaning, units, display rules, comparability, and derivation constraints.

Add a base time-series observation fact at a grain of metric, occupation, geography, period, source release, and comparability mode.

Add a derived-series fact for computed metrics such as year-over-year change, rolling averages, rank delta, and state-versus-national gap.

Add a time-period dimension or equivalent formal time model.

Keep raw published measures separate from derived measures.

Keep as-published history separate from comparable-history products.

## 4. Initial Metric Scope

Release 1 should focus on a small metric set:
employment_count,
mean_annual_wage,
median_annual_wage,
and projection-related measures where available.

Release 1 should focus on annual series first.

Release 1 should focus on national and state geography first.

## 5. Derived Metric Requirements

The first derived metric library should include:
year-over-year absolute change,
year-over-year percent change,
rolling average,
state-versus-national gap,
rank change over time,
and projection context or projection gap where valid.

Each derived metric must declare whether it requires comparable-history inputs.

Derived metrics must be stored and exposed separately from source observations.

## 6. Pipeline Requirements

The pipeline must build the new time-series layer from the existing warehouse facts rather than bypassing the current model.

The pipeline must populate the metric catalog.

The pipeline must normalize selected fact measures into base observations.

The pipeline must build comparable-history series where supported.

The pipeline must compute derived series.

The pipeline must compute ranking snapshots or equivalent rank-based products.

The pipeline must publish analyst-facing marts for the website and analysis layer.

## 7. Validation Requirements

Add validation for series continuity, period ordering, duplicate periods, and missing expected periods.

Add validation for derived-series correctness.

Add validation that comparable-only metrics are not built from non-comparable series.

Add validation for clear separation of observed values, derived values, and projected values.

Add validation that sufficient real local data exists to exercise visible website flows.

## 8. Reporting Mart Requirements

Add an occupation_trend_series mart.

Add an occupation_geography_gap_series mart.

Add an occupation_rank_change mart.

Add an occupation_projection_context mart.

Add an occupation_similarity_trend_overlay mart or equivalent if supported in the release.

All marts must preserve lineage, comparability mode, metric identity, and time semantics.

## 9. Website Requirements

Add a top-level Trends or Analysis area.

Add a trend explorer page for one occupation across time.

Add an occupation comparison page for multiple occupations across the same metric and period range.

Add a geography comparison page for one occupation across geographies.

Add a ranked movers page for largest gainers and losers over a selected period.

Extend the methodology page to explain comparability mode, derived metrics, revisions, and discontinuities.

Every trend-facing page must visibly show metric name, units, time grain, comparability mode, and lineage context.

Projected values must be visually distinct from observed values.

Derived values must be labeled as derived.

## 10. Acceptance Criteria

The real extract stage must be executed early and source files must be stored locally.

The full time-series pipeline must run against representative local real data, not only mocks.

The website must be launched against locally built real data.

A reviewer or agent must open and verify the key pages with visible real data:
trend explorer,
occupation comparison,
geography comparison,
ranked movers,
and methodology.

At least one end-to-end example must be verified from extraction through visible website output.

“Working” for this phase means the deployed application is exercised through the user-visible website on representative real data, not just that code and tests exist.

## 11. Out of Scope for Initial Release

Do not start with high-frequency series.

Do not start with real-time data.

Do not start with broad macroeconomic integration.

Do not start with machine-learned forecasting.

Do not start with international harmonization.

Do not let the first release expand beyond annual occupation trend analysis with a disciplined metric set.

## 12. Future Directions

Future releases may add inflation adjustment, per-capita measures, broader economic context series, job-posting data, transition scoring, opportunity scoring, event annotations, and saved analytical workspaces.

These should be built on the same observation-centric design rather than through separate one-off features.
