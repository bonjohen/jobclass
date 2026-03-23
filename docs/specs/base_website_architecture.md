# Reporting Website Top Level Architecture Document

## 1. Purpose

This document describes the top-level architecture of the labor market reporting website. The project presents occupation, wage, geography, skills, tasks, and trend data through a structured analytical web experience. It is designed to demonstrate strong data engineering, analytics, tool-building, and product-thinking skills.

This is a component-level architecture document. It defines the major parts of the system, their responsibilities, and how they relate to one another. It does not attempt to describe low-level implementation details.

## 2. Architectural Goals

The system should separate data acquisition, normalization, analytical storage, publishing, and presentation into clear layers. It should make source lineage visible, support version-aware reporting, allow semantic enrichment through O*NET-style descriptors, and expose a reporting experience that is useful both as an analytical product and as a portfolio artifact.

The architecture should support three kinds of outcomes. First, it should support reliable publication of occupation-centric analytical datasets. Second, it should support a website experience optimized for exploration, comparison, and methodology transparency. Third, it should support future extension into richer comparison, similarity, and mapping features without requiring redesign of the core data model.

## 3. Assumptions

This design assumes the technologies discussed earlier are used for pipeline orchestration, transformation, storage, application API, front-end presentation, and deployment. Those choices are treated as settled. This document focuses on system shape and boundaries rather than explaining those tools.

This design also assumes the primary external data sources are SOC, OEWS, O*NET, and optionally Employment Projections. It assumes the project exposes both warehouse-style modeled data and curated reporting views.

## 4. System Overview

The project is composed of six major areas.

The first area is source ingestion, which acquires and preserves raw external datasets.

The second area is data processing, which parses, validates, normalizes, versions, and loads data into analytical storage.

The third area is analytical storage, which contains conformed dimensions, facts, semantic bridges, and reporting marts.

The fourth area is publication services, which expose reporting-ready data to the website through a stable application layer.

The fifth area is the reporting website itself, which provides the user-facing analytical experience.

The sixth area is operational governance, which captures run metadata, validation results, lineage, and quality reporting.

These areas are intentionally separated so that source behavior, analytical truth, and presentation concerns do not become entangled.

## 5. Major Components

## 5.1 Source Ingestion Layer

The source ingestion layer is responsible for acquiring source files, capturing source metadata, preserving immutable raw artifacts, and registering each acquisition event.

Its responsibilities include identifying configured datasets, downloading artifacts, recording checksums and release identifiers, and storing source snapshots in a durable raw zone.

Its outputs are raw files plus ingestion metadata.

It does not perform business modeling, analytical joins, or user-facing transformations.

## 5.2 Parsing and Standardization Layer

The parsing and standardization layer converts heterogeneous source files into predictable staged datasets.

Its responsibilities include source-specific parsing, schema normalization, explicit typing, null handling, identifier normalization, release metadata extraction, and stage-level record preparation.

Its outputs are structured staging tables aligned to consistent internal naming and data conventions.

It does not define conformed analytical truth or presentation-layer views.

## 5.3 Validation and Quality Layer

The validation and quality layer evaluates whether parsed and transformed data is safe to publish.

Its responsibilities include structural validation, business-grain validation, referential integrity checks, source-to-model mapping checks, reconciliation checks, drift detection, and release consistency checks.

Its outputs are validation results, quality reports, exception records, and publication gates.

It is a control layer, not a storage layer. Its purpose is to decide whether downstream publication should proceed.

## 5.4 Core Analytical Warehouse

The core analytical warehouse is the durable modeled data layer.

Its responsibilities include maintaining conformed dimensions such as occupation, geography, industry, and semantic descriptors; maintaining fact tables such as employment, wages, and projections; maintaining bridge tables for skills, tasks, knowledge, and abilities; and preserving version-aware historical state.

This layer is the analytical source of truth for the project.

It does not expose raw source formats, and it does not optimize for direct end-user browsing.

## 5.5 Reporting Mart Layer

The reporting mart layer provides curated, query-friendly datasets shaped around specific reporting use cases.

Its responsibilities include denormalizing selected warehouse logic, precomputing hierarchy rollups, preparing occupation profiles, supporting geography comparisons, exposing semantic profiles, and simplifying common website queries.

Its outputs are reporting-ready views and materialized datasets such as occupation summaries, occupation wage profiles, occupation skill profiles, trend views, and similarity seed views.

This layer is designed for usability and consistency, not for raw source preservation.

## 5.6 Application Service Layer

The application service layer provides the stable interface between analytical data and the reporting website.

Its responsibilities include exposing search, filter, comparison, detail, and metadata endpoints; enforcing consistent query patterns; packaging chart and table payloads; and surfacing lineage, version, and methodology information where needed.

This layer isolates the website from warehouse complexity and allows the reporting experience to remain stable even if the underlying data model evolves.

It should expose business-oriented resources such as occupations, geography comparisons, skill profiles, task profiles, trend views, and methodology metadata rather than raw warehouse tables.

## 5.7 Website Presentation Layer

The website presentation layer is the user-facing reporting product.

Its responsibilities include page layout, navigation, occupation search, hierarchy browsing, geography comparison, skill and task exploration, trend display, source transparency, methodology presentation, and portfolio framing.

It should present the data as a coherent analytical product rather than a loose collection of charts.

The major experience areas are likely to include an overview page, occupation profile pages, geography comparison pages, skill and task exploration pages, trend pages, and methodology pages.

## 5.8 Observability and Operational Metadata Layer

This layer provides visibility into system behavior.

Its responsibilities include run manifests, dataset audit records, parser versions, validation outcomes, publication history, row-count deltas, schema drift events, and failure classifications.

Its purpose is to make the system inspectable and trustworthy.

It supports maintainers directly and also supplies selected metadata to the reporting site, especially on methodology and data lineage pages.

## 6. Logical Data Flow

The logical flow begins when configured external datasets are acquired into the raw ingestion layer. Those artifacts are then parsed and standardized into stage-level datasets. The validation layer evaluates the staged and transformed data. If validation succeeds, the conformed warehouse is updated and the reporting marts are refreshed. The application service layer exposes the reporting-ready data and metadata. The website then renders analytical views for search, browsing, comparison, and explanation.

A separate operational flow captures run history, validation results, and publication records throughout the process.

## 7. Website-Facing Functional Domains

The architecture should support a small number of clear reporting domains.

The occupation domain supports search, hierarchy, profile views, wages, employment, and related descriptors.

The geography domain supports state and metro comparison, occupation distribution, and regional wage analysis.

The semantic domain supports skills, tasks, knowledge, abilities, and occupation similarity entry points.

The trend domain supports historical and projected views, with clear distinction between as-published and comparable-history perspectives.

The methodology domain supports data-source explanation, lineage, validation summaries, release metadata, and project intent.

These domains should be visible both in the reporting mart design and in the application service boundary.

## 8. Cross-Cutting Concerns

Several concerns span the entire system.

Versioning is cross-cutting. Every major component must preserve release identity and reference-period meaning.

Lineage is cross-cutting. The system must always be able to explain where a published value came from.

Validation is cross-cutting. Publication must depend on explicit quality checks rather than trust in the pipeline.

Consistency is cross-cutting. Occupation codes, geography codes, semantic identifiers, and naming conventions must remain stable across layers.

Usability is cross-cutting. The application layer and reporting mart layer must shape data around real user questions, not just reflect warehouse internals.

Portfolio value is cross-cutting. The project should expose enough methodology, lineage, and inspectable outputs to demonstrate judgment and tool-building discipline.

## 9. Primary Artifacts

The architecture should produce a set of durable artifacts beyond the website itself.

These include source manifests, raw dataset snapshots, run manifests, validation reports, conformed warehouse tables, reporting marts, application-service contracts, methodology content, and selected sample analyses or notebooks.

A reviewer should be able to see evidence of ingestion, modeling, publication, and presentation as distinct but coordinated parts of one system.

## 10. Future Expansion Paths

The architecture is intentionally shaped to allow later additions without redesigning the core.

A title-normalization and title-to-occupation mapping domain can be added later as a separate component attached to the occupation backbone.

Additional semantic analytics such as similarity scoring, clustering, and skill-gap analysis can be added by building on the semantic descriptor bridges and reporting marts.

Internal HR or job-posting data can be added later as mapped layers rather than redefining the core data model.

Additional public sources can be integrated by extending the ingestion, staging, and validation layers while preserving the same publication model.

## 11. Summary

At the top level, this project is a layered analytical reporting system with clear boundaries between source ingestion, data processing, analytical truth, reporting views, application services, and user presentation.

The architecture is intentionally designed to show disciplined data work rather than just website construction. It presents a system where the reporting experience is only the visible surface of a larger, well-structured analytical product.
