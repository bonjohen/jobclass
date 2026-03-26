/* Pipeline Explorer — Graph Data Model
 *
 * Static graph data describing the full JobClass pipeline.
 * Consumed by pipeline.js for rendering.
 * No fetch calls — this is a self-contained JS data file.
 *
 * Content mined from the real repository: schema, parsers, loaders,
 * validators, API routes, CLI commands, lesson map, and build scripts.
 */

"use strict";

/* --- Node Type Constants (PE1-01) --- */
var NODE_TYPES = {
    SOURCE: "source",
    PROCESS: "process",
    STORAGE: "storage",
    GATE: "gate",
    INTERFACE: "interface",
    LESSON: "lesson"
};

/* --- Edge Type Constants (PE1-02) --- */
var EDGE_TYPES = {
    REQUIRED: "required",
    CONDITIONAL: "conditional",
    BLOCKED: "blocked",
    OPTIONAL: "optional",
    EDUCATIONAL: "educational",
    DERIVED: "derived"
};

/* --- Lane/Group Definitions (PE1-03) --- */
var LANES = [
    { id: "sources",    label: "Federal Data Sources",     color: "#e8f4fd", x: 0,    y: 0,   w: 220, h: 700 },
    { id: "extraction", label: "Extraction & Acquisition", color: "#fef3e2", x: 240,  y: 0,   w: 180, h: 700 },
    { id: "raw",        label: "Raw Landing",              color: "#fce4ec", x: 440,  y: 0,   w: 180, h: 700 },
    { id: "staging",    label: "Staging & Parsing",        color: "#e8f5e9", x: 640,  y: 0,   w: 220, h: 700 },
    { id: "validation", label: "Validation Gates",         color: "#fff3e0", x: 880,  y: 0,   w: 180, h: 700 },
    { id: "core",       label: "Core Warehouse",           color: "#e3f2fd", x: 1080, y: 0,   w: 240, h: 700 },
    { id: "timeseries", label: "Time-Series Enrichment",   color: "#f3e5f5", x: 1340, y: 0,   w: 200, h: 700 },
    { id: "marts",      label: "Analyst Marts",            color: "#e0f2f1", x: 1560, y: 0,   w: 200, h: 700 },
    { id: "api_web",    label: "API & Web Pages",          color: "#fff9c4", x: 1780, y: 0,   w: 240, h: 700 },
    { id: "deployment", label: "Build & Deployment",       color: "#efebe9", x: 2040, y: 0,   w: 200, h: 700 }
];

/* --- Node Definitions --- */

/* PE1-04: Source Nodes */
var SOURCE_NODES = [
    {
        id: "src_soc", type: NODE_TYPES.SOURCE, lane: "sources",
        label: "SOC Taxonomy", x: 60, y: 60,
        purpose: "Standard Occupational Classification — the backbone taxonomy for all occupation codes.",
        cadence: "Periodic (major revisions ~10 years, minor updates more often)",
        artifact: "XLSX / CSV hierarchy and definitions files",
        caveats: "SOC 2018 XLSX uses short group labels; older CSV uses full labels. Parser LEVEL_MAP handles both.",
        metadata: { datasets: ["soc_hierarchy", "soc_definitions"], parser_version: "1.0.0" }
    },
    {
        id: "src_oews", type: NODE_TYPES.SOURCE, lane: "sources",
        label: "OEWS Survey", x: 60, y: 150,
        purpose: "Occupational Employment and Wage Statistics — employment counts and wage measures by occupation and geography.",
        cadence: "Annual (May reference period)",
        artifact: "XLSX files from BLS",
        caveats: "BLS blocks bare HTTP requests — requires browser-like Sec-Fetch-* headers. Columns are UPPERCASE.",
        metadata: { datasets: ["oews_national", "oews_state"], parser_version: "1.0.0" }
    },
    {
        id: "src_onet", type: NODE_TYPES.SOURCE, lane: "sources",
        label: "O*NET", x: 60, y: 240,
        purpose: "Occupational Information Network — skills, knowledge, abilities, tasks, work activities, education, and technology descriptors.",
        cadence: "Semi-annual updates",
        artifact: "CSV/XLSX files from O*NET Resource Center",
        caveats: "O*NET uses SOC-like codes with .00 suffix extensions. Seven separate descriptor domains.",
        metadata: { datasets: ["onet_skills", "onet_knowledge", "onet_abilities", "onet_tasks", "onet_work_activities", "onet_education", "onet_technology_skills"], parser_version: "1.0.0" }
    },
    {
        id: "src_projections", type: NODE_TYPES.SOURCE, lane: "sources",
        label: "BLS Projections", x: 60, y: 330,
        purpose: "Employment Projections — forward-looking employment estimates from the National Employment Matrix.",
        cadence: "Biennial (10-year horizon)",
        artifact: "XLSX from BLS",
        caveats: "Employment stored in thousands (309.4 = 309,400). 5 NEM 2024 codes don't map to SOC 2018.",
        metadata: { datasets: ["bls_employment_projections"], parser_version: "1.1.0" }
    },
    {
        id: "src_cpi", type: NODE_TYPES.SOURCE, lane: "sources",
        label: "BLS CPI-U", x: 60, y: 420,
        purpose: "Consumer Price Index for All Urban Consumers — used for inflation adjustment of nominal wages.",
        cadence: "Monthly",
        artifact: "BLS public data API / flat files",
        caveats: "Deflation base year is 2023. Formula: real_wage = nominal * (CPI_2023 / CPI_year).",
        metadata: { datasets: ["bls_cpi"], parser_version: "1.0.0" }
    },
    {
        id: "src_crosswalk", type: NODE_TYPES.SOURCE, lane: "sources",
        label: "SOC Crosswalk", x: 60, y: 510,
        purpose: "SOC 2010-to-2018 occupation code mappings for historical comparability.",
        cadence: "One-time per SOC revision pair",
        artifact: "XLSX mapping file",
        caveats: "Mapping types: 1:1, split, merge, complex. Only 1:1 used for wage comparison; splits/merges for employment counts.",
        metadata: { datasets: ["soc_crosswalk"], parser_version: "1.0.0" }
    }
];

/* PE1-05: Extraction/Acquisition Nodes */
var EXTRACTION_NODES = [
    {
        id: "proc_download_mgr", type: NODE_TYPES.PROCESS, lane: "extraction",
        label: "Download Manager", x: 290, y: 100,
        purpose: "Declarative, manifest-driven download engine. Fetches source artifacts by URL with browser-like headers.",
        artifact: "Downloaded files written to raw landing paths",
        metadata: { file: "src/jobclass/extract/download.py", cli: "jobclass-pipeline run-all" }
    },
    {
        id: "proc_run_manifest", type: NODE_TYPES.PROCESS, lane: "extraction",
        label: "Run Manifest", x: 290, y: 220,
        purpose: "Tracks each pipeline execution: run ID, timestamps, source URLs, and checksums for reproducibility.",
        artifact: "Manifest metadata per run",
        metadata: { file: "src/jobclass/extract/manifest.py" }
    },
    {
        id: "proc_browser_headers", type: NODE_TYPES.PROCESS, lane: "extraction",
        label: "Browser Header\nWorkaround", x: 290, y: 340,
        purpose: "Injects Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, Sec-Fetch-User headers to bypass BLS blocking.",
        artifact: "HTTP headers on every BLS request",
        caveats: "BLS.gov rejects requests without these headers.",
        metadata: { file: "src/jobclass/extract/download.py" }
    }
];

/* PE1-06: Raw Landing Nodes */
var RAW_NODES = [
    {
        id: "store_raw_soc", type: NODE_TYPES.STORAGE, lane: "raw",
        label: "Raw SOC Files", x: 490, y: 60,
        purpose: "Immutable capture of SOC hierarchy and definitions source files.",
        metadata: { path_pattern: "raw/soc/{dataset}/{release_id}/{run_id}/{filename}" }
    },
    {
        id: "store_raw_oews", type: NODE_TYPES.STORAGE, lane: "raw",
        label: "Raw OEWS Files", x: 490, y: 150,
        purpose: "Immutable capture of OEWS XLSX files (national and state employment/wages).",
        metadata: { path_pattern: "raw/bls/oews_{geo}/{release_id}/{run_id}/{filename}" }
    },
    {
        id: "store_raw_onet", type: NODE_TYPES.STORAGE, lane: "raw",
        label: "Raw O*NET Files", x: 490, y: 240,
        purpose: "Immutable capture of O*NET descriptor CSV/XLSX files (7 domains).",
        metadata: { path_pattern: "raw/onet/{dataset}/{release_id}/{run_id}/{filename}" }
    },
    {
        id: "store_raw_proj", type: NODE_TYPES.STORAGE, lane: "raw",
        label: "Raw Projections\nFiles", x: 490, y: 330,
        purpose: "Immutable capture of BLS Employment Projections XLSX.",
        metadata: { path_pattern: "raw/bls/employment_projections/{release_id}/{run_id}/{filename}" }
    },
    {
        id: "store_raw_cpi", type: NODE_TYPES.STORAGE, lane: "raw",
        label: "Raw CPI Files", x: 490, y: 420,
        purpose: "Immutable capture of CPI-U data files.",
        metadata: { path_pattern: "raw/bls/cpi/{release_id}/{run_id}/{filename}" }
    },
    {
        id: "store_raw_xwalk", type: NODE_TYPES.STORAGE, lane: "raw",
        label: "Raw Crosswalk\nFiles", x: 490, y: 510,
        purpose: "Immutable capture of SOC 2010-2018 crosswalk mapping XLSX.",
        metadata: { path_pattern: "raw/soc/crosswalk/{release_id}/{run_id}/{filename}" }
    }
];

/* PE1-07: Staging/Parsing Nodes */
var STAGING_NODES = [
    {
        id: "proc_parse_soc", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "SOC Parser", x: 710, y: 40,
        purpose: "Parses SOC hierarchy XLSX/CSV into standardized staging tables.",
        metadata: { file: "src/jobclass/parse/soc.py", tables: ["stage__soc__hierarchy", "stage__soc__definitions"] }
    },
    {
        id: "proc_parse_oews", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "OEWS Parser", x: 710, y: 120,
        purpose: "Parses OEWS XLSX with UPPERCASE column normalization via _OEWS_COLUMN_ALIASES.",
        metadata: { file: "src/jobclass/parse/oews.py", tables: ["stage__bls__oews_national", "stage__bls__oews_state"] }
    },
    {
        id: "proc_parse_onet", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "O*NET Parser", x: 710, y: 200,
        purpose: "Parses 7 O*NET descriptor domains into separate staging tables.",
        metadata: { file: "src/jobclass/parse/onet.py", tables: ["stage__onet__skills", "stage__onet__knowledge", "stage__onet__abilities", "stage__onet__tasks", "stage__onet__work_activities", "stage__onet__education", "stage__onet__technology_skills"] }
    },
    {
        id: "proc_parse_proj", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "Projections\nParser", x: 710, y: 300,
        purpose: "Parses BLS Projections XLSX, converting employment from thousands to whole numbers.",
        metadata: { file: "src/jobclass/parse/projections.py", tables: ["stage__bls__employment_projections"] }
    },
    {
        id: "proc_parse_cpi", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "CPI Parser", x: 710, y: 400,
        purpose: "Parses CPI-U data into staging tables for price index observations.",
        metadata: { file: "src/jobclass/parse/cpi.py", tables: ["stage__bls__cpi"] }
    },
    {
        id: "proc_parse_cpi_domain", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "CPI Domain\nParser", x: 710, y: 480,
        purpose: "Full CPI domain parser: series metadata, item hierarchy, publication levels, importance, prices.",
        metadata: { file: "src/jobclass/parse/cpi_domain.py", tables: ["stage__bls__cpi_series", "stage__bls__cpi_item_hierarchy", "stage__bls__cpi_publication_level", "stage__bls__cpi_relative_importance", "stage__bls__cpi_average_price"] }
    },
    {
        id: "proc_parse_xwalk", type: NODE_TYPES.PROCESS, lane: "staging",
        label: "Crosswalk Parser", x: 710, y: 560,
        purpose: "Parses SOC 2010-2018 crosswalk, classifying mapping types (1:1, split, merge, complex).",
        metadata: { file: "src/jobclass/parse/soc.py", tables: ["stage__soc__crosswalk"] }
    }
];

/* PE1-08: Validation Gate Nodes */
var VALIDATION_NODES = [
    {
        id: "gate_schema_drift", type: NODE_TYPES.GATE, lane: "validation",
        label: "Schema Drift\nDetection", x: 940, y: 60,
        purpose: "Blocks warehouse publication if source columns change. Fail-fast on missing/changed columns.",
        metadata: { file: "src/jobclass/validate/framework.py", functions: ["validate_required_columns", "validate_column_types"] }
    },
    {
        id: "gate_referential", type: NODE_TYPES.GATE, lane: "validation",
        label: "Referential\nIntegrity", x: 940, y: 170,
        purpose: "Ensures facts and bridges point to existing dimension records.",
        metadata: { file: "src/jobclass/validate/framework.py", functions: ["validate_referential_integrity"] }
    },
    {
        id: "gate_grain", type: NODE_TYPES.GATE, lane: "validation",
        label: "Grain\nUniqueness", x: 940, y: 280,
        purpose: "Prevents duplicate business keys. Verifies idempotent re-run safety.",
        metadata: { file: "src/jobclass/validate/framework.py", functions: ["validate_grain_uniqueness", "validate_append_only"] }
    },
    {
        id: "gate_null_semantics", type: NODE_TYPES.GATE, lane: "validation",
        label: "Null Semantics\nPreservation", x: 940, y: 390,
        purpose: "Ensures suppressed/missing OEWS values remain null — never imputed.",
        metadata: { file: "src/jobclass/validate/oews.py" }
    },
    {
        id: "gate_temporal", type: NODE_TYPES.GATE, lane: "validation",
        label: "Temporal\nConsistency", x: 940, y: 500,
        purpose: "Validates version monotonicity, period ordering, and source-vs-business time integrity.",
        metadata: { file: "src/jobclass/validate/framework.py", functions: ["validate_version_monotonicity"] }
    },
    {
        id: "gate_soc_alignment", type: NODE_TYPES.GATE, lane: "validation",
        label: "SOC Alignment", x: 940, y: 610,
        purpose: "Validates that OEWS, O*NET, and Projections occupation codes map to dim_occupation.",
        metadata: { files: ["src/jobclass/validate/oews.py", "src/jobclass/validate/onet.py", "src/jobclass/validate/projections.py"] }
    }
];

/* PE1-09: Core Warehouse Nodes */
var CORE_NODES = [
    {
        id: "store_dim_occupation", type: NODE_TYPES.STORAGE, lane: "core",
        label: "dim_occupation", x: 1150, y: 40,
        purpose: "Conformed occupation dimension — SOC codes, titles, definitions, hierarchy levels, and version tracking.",
        metadata: { loader: "src/jobclass/load/soc.py", grain: "soc_code + source_release_id" }
    },
    {
        id: "store_dim_geography", type: NODE_TYPES.STORAGE, lane: "core",
        label: "dim_geography", x: 1150, y: 110,
        purpose: "Geographic dimension — national, state, and MSA areas.",
        metadata: { loader: "src/jobclass/load/oews.py" }
    },
    {
        id: "store_dim_descriptors", type: NODE_TYPES.STORAGE, lane: "core",
        label: "Descriptor\nDimensions", x: 1150, y: 180,
        purpose: "dim_skill, dim_knowledge, dim_ability, dim_task, dim_work_activity, dim_education_requirement, dim_technology",
        metadata: { loader: "src/jobclass/load/onet.py", tables: ["dim_skill", "dim_knowledge", "dim_ability", "dim_task", "dim_work_activity", "dim_education_requirement", "dim_technology"] }
    },
    {
        id: "store_fact_wages", type: NODE_TYPES.STORAGE, lane: "core",
        label: "fact_occupation_\nemployment_wages", x: 1150, y: 270,
        purpose: "OEWS employment counts and wage measures by occupation, geography, and vintage.",
        metadata: { loader: "src/jobclass/load/oews.py", grain: "soc_code + geo_code + source_release_id" }
    },
    {
        id: "store_fact_proj", type: NODE_TYPES.STORAGE, lane: "core",
        label: "fact_occupation_\nprojections", x: 1150, y: 360,
        purpose: "BLS employment projections (base year, projected year, employment change).",
        metadata: { loader: "src/jobclass/load/projections.py" }
    },
    {
        id: "store_bridges", type: NODE_TYPES.STORAGE, lane: "core",
        label: "Bridge Tables", x: 1150, y: 440,
        purpose: "M-to-M: bridge_occupation_skill, _knowledge, _ability, _task, _work_activity, _education, _technology, _hierarchy",
        metadata: { loader: "src/jobclass/load/onet.py" }
    },
    {
        id: "store_dim_cpi", type: NODE_TYPES.STORAGE, lane: "core",
        label: "CPI Dimensions\n& Facts", x: 1150, y: 530,
        purpose: "dim_price_index, dim_cpi_member, dim_cpi_area, fact_price_index_observation, fact_cpi_observation, bridge_cpi_*",
        metadata: { loaders: ["src/jobclass/load/cpi.py", "src/jobclass/load/cpi_domain.py"] }
    },
    {
        id: "store_crosswalk", type: NODE_TYPES.STORAGE, lane: "core",
        label: "SOC Crosswalk\nMappings", x: 1150, y: 620,
        purpose: "SOC 2010-to-2018 code mappings with type classification (1:1, split, merge, complex).",
        metadata: { loader: "src/jobclass/load/soc.py" }
    }
];

/* PE1-10: Time-Series Enrichment Nodes */
var TIMESERIES_NODES = [
    {
        id: "proc_ts_metrics", type: NODE_TYPES.PROCESS, lane: "timeseries",
        label: "Metric Catalog\nBuilder", x: 1400, y: 80,
        purpose: "Populates dim_metric with 6 base metrics: employment_count, mean/median wage, projected employment, change, pct change.",
        metadata: { file: "src/jobclass/load/timeseries.py", function: "populate_dim_metric" }
    },
    {
        id: "proc_ts_periods", type: NODE_TYPES.PROCESS, lane: "timeseries",
        label: "Time Period\nBuilder", x: 1400, y: 180,
        purpose: "Creates dim_time_period with annual period dimension records.",
        metadata: { file: "src/jobclass/load/timeseries.py", function: "populate_dim_time_period" }
    },
    {
        id: "proc_ts_observations", type: NODE_TYPES.PROCESS, lane: "timeseries",
        label: "Multi-Vintage\nOEWS Loading", x: 1400, y: 280,
        purpose: "Aggregates OEWS observations into fact_time_series_observation with comparable/as-published modes.",
        metadata: { file: "src/jobclass/load/timeseries.py", function: "populate_fact_time_series_observation" }
    },
    {
        id: "proc_ts_cpi_deflation", type: NODE_TYPES.PROCESS, lane: "timeseries",
        label: "CPI Deflation", x: 1400, y: 380,
        purpose: "Applies CPI-U deflation for real wage metrics. Base year: 2023. Formula: real = nominal * (CPI_2023 / CPI_year).",
        metadata: { file: "src/jobclass/load/timeseries.py", constant: "CPI_BASE_YEAR = 2023" }
    },
    {
        id: "proc_ts_derived", type: NODE_TYPES.PROCESS, lane: "timeseries",
        label: "Derived Series\nComputation", x: 1400, y: 480,
        purpose: "Calculates year-over-year changes, percent changes, and stores in fact_derived_series.",
        metadata: { file: "src/jobclass/load/timeseries.py", function: "populate_fact_derived_series" }
    },
    {
        id: "proc_ts_comparable", type: NODE_TYPES.PROCESS, lane: "timeseries",
        label: "Comparable\nHistory Logic", x: 1400, y: 580,
        purpose: "Uses SOC crosswalk to build comparable history across SOC revisions. Only 1:1 mappings for wages; splits/merges for employment.",
        metadata: { file: "src/jobclass/load/timeseries.py" }
    }
];

/* PE1-11: Mart Nodes */
var MART_NODES = [
    {
        id: "store_mart_summary", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "occupation_\nsummary", x: 1620, y: 60,
        purpose: "One row per current occupation with hierarchy fields — the main lookup mart.",
        metadata: { grain: "soc_code" }
    },
    {
        id: "store_mart_wages_geo", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "occupation_wages_\nby_geography", x: 1620, y: 150,
        purpose: "Employment and wage measures by occupation and geography — powers wage comparison views.",
        metadata: { grain: "soc_code + geo_code + source_release_id" }
    },
    {
        id: "store_mart_skill_profile", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "occupation_skill_\nprofile", x: 1620, y: 240,
        purpose: "Occupation-to-skill relationships with importance and level scores.",
        metadata: { grain: "soc_code + skill_id" }
    },
    {
        id: "store_mart_trend", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "mart_occupation_\ntrend_series", x: 1620, y: 330,
        purpose: "Trends over time per occupation, metric, and geography — powers trend explorer.",
        metadata: { grain: "soc_code + metric_id + geo_code + period" }
    },
    {
        id: "store_mart_geo_gap", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "mart_occupation_\ngeo_gap_series", x: 1620, y: 420,
        purpose: "State vs. national wage gaps over time — powers geography comparison.",
        metadata: { grain: "soc_code + geo_code + period" }
    },
    {
        id: "store_mart_rank", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "mart_occupation_\nrank_change", x: 1620, y: 510,
        purpose: "Year-over-year ranking changes — powers ranked movers page.",
        metadata: { grain: "soc_code + metric_id + period" }
    },
    {
        id: "store_mart_similarity", type: NODE_TYPES.STORAGE, lane: "marts",
        label: "occupation_\nsimilarity_seeded", x: 1620, y: 600,
        purpose: "Jaccard cosine similarity on skill importance vectors between occupations.",
        metadata: { grain: "soc_code_a + soc_code_b" }
    }
];

/* PE1-12: API/Web/Interface Nodes */
var INTERFACE_NODES = [
    {
        id: "iface_search", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Search Page", x: 1860, y: 30,
        purpose: "Occupation search by keyword or SOC code.",
        metadata: { route: "/search", api: "/api/occupations/search", template: "search.html" }
    },
    {
        id: "iface_hierarchy", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Hierarchy\nBrowser", x: 1860, y: 90,
        purpose: "Interactive SOC hierarchy tree browser.",
        metadata: { route: "/hierarchy", api: "/api/occupations/hierarchy", template: "hierarchy.html" }
    },
    {
        id: "iface_occupation", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Occupation\nProfile", x: 1860, y: 160,
        purpose: "Detailed occupation page: wages, skills, knowledge, abilities, tasks, projections, similar occupations.",
        metadata: { route: "/occupation/{soc_code}", apis: ["/api/occupations/{soc_code}", "/api/occupations/{soc_code}/skills", "/api/occupations/{soc_code}/wages"], template: "occupation.html" }
    },
    {
        id: "iface_wages", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Wage\nComparison", x: 1860, y: 240,
        purpose: "State-level wage comparison for a given occupation.",
        metadata: { route: "/occupation/{soc_code}/wages", api: "/api/occupations/{soc_code}/wages", template: "wages_comparison.html" }
    },
    {
        id: "iface_trend_explorer", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Trend Explorer", x: 1860, y: 310,
        purpose: "Time-series charts for a single occupation — employment, wages, projections over time.",
        metadata: { route: "/trends/explorer/{soc_code}", api: "/api/trends/{soc_code}", template: "trend_explorer.html" }
    },
    {
        id: "iface_occ_compare", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Occupation\nComparison", x: 1860, y: 380,
        purpose: "Compare the same metric across multiple occupations over time.",
        metadata: { route: "/trends/compare", api: "/api/trends/compare/occupations", template: "occupation_comparison.html" }
    },
    {
        id: "iface_geo_compare", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Geography\nComparison", x: 1860, y: 450,
        purpose: "Compare an occupation's metrics across states for a given year.",
        metadata: { route: "/trends/geography/{soc_code}", api: "/api/trends/compare/geography", template: "geography_comparison.html" }
    },
    {
        id: "iface_movers", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Ranked Movers", x: 1860, y: 520,
        purpose: "Top gainers and losers by employment, wage, or projection metrics.",
        metadata: { route: "/trends/movers", api: "/api/trends/movers", template: "ranked_movers.html" }
    },
    {
        id: "iface_cpi", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "CPI Explorer", x: 1860, y: 590,
        purpose: "Interactive CPI member hierarchy browser with series, areas, and prices.",
        metadata: { routes: ["/cpi", "/cpi/explorer", "/cpi/member/{code}", "/cpi/area/{code}"], template: "cpi_explorer.html" }
    },
    {
        id: "iface_methodology", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Methodology", x: 1860, y: 650,
        purpose: "Documents data sources, metrics, validation approach, and analytical methods.",
        metadata: { route: "/methodology", template: "methodology.html" }
    },
    {
        id: "iface_lessons", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Lessons Section", x: 1960, y: 30,
        purpose: "20 educational lessons on data engineering, from federal data to fetch shim architecture.",
        metadata: { route: "/lessons", template: "lessons.html", count: 20 }
    },
    {
        id: "iface_pipeline", type: NODE_TYPES.INTERFACE, lane: "api_web",
        label: "Pipeline\nExplorer", x: 1960, y: 110,
        purpose: "This page — interactive canvas-based visualization of the entire JobClass pipeline.",
        metadata: { route: "/pipeline", template: "pipeline.html" }
    }
];

/* PE1-13: Deployment/Static Nodes */
var DEPLOYMENT_NODES = [
    {
        id: "proc_build_static", type: NODE_TYPES.PROCESS, lane: "deployment",
        label: "Static Site\nBuilder", x: 2100, y: 80,
        purpose: "Pre-renders all HTML pages via FastAPI TestClient and generates static JSON API responses.",
        metadata: { file: "scripts/build_static.py", cli: "python scripts/build_static.py --base-path /jobclass" }
    },
    {
        id: "proc_fetch_shim", type: NODE_TYPES.PROCESS, lane: "deployment",
        label: "Fetch Shim\nInjection", x: 2100, y: 200,
        purpose: "Injects client-side JavaScript shim into HTML pages to intercept fetch() calls and redirect to static JSON.",
        metadata: { file: "scripts/build_static.py" }
    },
    {
        id: "proc_deploy", type: NODE_TYPES.PROCESS, lane: "deployment",
        label: "Deploy to\nGitHub Pages", x: 2100, y: 320,
        purpose: "Force-pushes _site/ to gh-pages branch. Includes .nojekyll file.",
        metadata: { file: "scripts/deploy_pages.py", url: "https://bonjohen.github.io/jobclass/" }
    },
    {
        id: "proc_health", type: NODE_TYPES.PROCESS, lane: "deployment",
        label: "Health Check", x: 2100, y: 440,
        purpose: "API health endpoint verifying database connectivity and table availability.",
        metadata: { api: "/api/health", file: "src/jobclass/web/api/health.py" }
    },
    {
        id: "proc_cli", type: NODE_TYPES.PROCESS, lane: "deployment",
        label: "CLI Commands", x: 2100, y: 560,
        purpose: "Pipeline orchestration: migrate, run-all, status, timeseries-refresh.",
        metadata: { file: "src/jobclass/cli.py", commands: ["migrate", "run-all", "status", "timeseries-refresh"] }
    }
];

/* Combine all nodes */
var GRAPH_NODES = [].concat(
    SOURCE_NODES,
    EXTRACTION_NODES,
    RAW_NODES,
    STAGING_NODES,
    VALIDATION_NODES,
    CORE_NODES,
    TIMESERIES_NODES,
    MART_NODES,
    INTERFACE_NODES,
    DEPLOYMENT_NODES
);

/* --- PE1-14: Edge Definitions --- */
var GRAPH_EDGES = [
    /* Sources → Extraction */
    { from: "src_soc",         to: "proc_download_mgr", type: EDGE_TYPES.REQUIRED },
    { from: "src_oews",        to: "proc_download_mgr", type: EDGE_TYPES.REQUIRED },
    { from: "src_onet",        to: "proc_download_mgr", type: EDGE_TYPES.REQUIRED },
    { from: "src_projections",  to: "proc_download_mgr", type: EDGE_TYPES.REQUIRED },
    { from: "src_cpi",         to: "proc_download_mgr", type: EDGE_TYPES.REQUIRED },
    { from: "src_crosswalk",   to: "proc_download_mgr", type: EDGE_TYPES.OPTIONAL },
    { from: "proc_download_mgr", to: "proc_run_manifest", type: EDGE_TYPES.REQUIRED },
    { from: "proc_download_mgr", to: "proc_browser_headers", type: EDGE_TYPES.REQUIRED, condition: "BLS sources only" },

    /* Extraction → Raw Landing */
    { from: "proc_download_mgr", to: "store_raw_soc",   type: EDGE_TYPES.REQUIRED },
    { from: "proc_download_mgr", to: "store_raw_oews",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_download_mgr", to: "store_raw_onet",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_download_mgr", to: "store_raw_proj",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_download_mgr", to: "store_raw_cpi",   type: EDGE_TYPES.REQUIRED },
    { from: "proc_download_mgr", to: "store_raw_xwalk", type: EDGE_TYPES.OPTIONAL },

    /* Raw → Parsing */
    { from: "store_raw_soc",   to: "proc_parse_soc",        type: EDGE_TYPES.REQUIRED },
    { from: "store_raw_oews",  to: "proc_parse_oews",       type: EDGE_TYPES.REQUIRED },
    { from: "store_raw_onet",  to: "proc_parse_onet",       type: EDGE_TYPES.REQUIRED },
    { from: "store_raw_proj",  to: "proc_parse_proj",       type: EDGE_TYPES.REQUIRED },
    { from: "store_raw_cpi",   to: "proc_parse_cpi",        type: EDGE_TYPES.REQUIRED },
    { from: "store_raw_cpi",   to: "proc_parse_cpi_domain", type: EDGE_TYPES.REQUIRED },
    { from: "store_raw_xwalk", to: "proc_parse_xwalk",      type: EDGE_TYPES.OPTIONAL },

    /* Parsing → Validation */
    { from: "proc_parse_soc",        to: "gate_schema_drift",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_parse_oews",       to: "gate_schema_drift",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_parse_onet",       to: "gate_schema_drift",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_parse_proj",       to: "gate_schema_drift",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_parse_cpi",        to: "gate_schema_drift",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_parse_cpi_domain", to: "gate_schema_drift",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_parse_xwalk",      to: "gate_schema_drift",  type: EDGE_TYPES.OPTIONAL },

    { from: "gate_schema_drift", to: "gate_referential",    type: EDGE_TYPES.REQUIRED, condition: "Schema valid" },
    { from: "gate_schema_drift", to: "gate_grain",          type: EDGE_TYPES.BLOCKED,  condition: "Schema drift blocks publication" },
    { from: "gate_referential",  to: "gate_grain",          type: EDGE_TYPES.REQUIRED },
    { from: "gate_grain",        to: "gate_null_semantics",  type: EDGE_TYPES.REQUIRED },
    { from: "gate_null_semantics", to: "gate_temporal",      type: EDGE_TYPES.REQUIRED },
    { from: "gate_temporal",     to: "gate_soc_alignment",   type: EDGE_TYPES.REQUIRED },

    /* Validation → Core Loading */
    { from: "gate_soc_alignment",  to: "store_dim_occupation",   type: EDGE_TYPES.REQUIRED, condition: "SOC loads first" },
    { from: "gate_soc_alignment",  to: "store_dim_geography",    type: EDGE_TYPES.REQUIRED },
    { from: "gate_soc_alignment",  to: "store_dim_descriptors",  type: EDGE_TYPES.REQUIRED },
    { from: "gate_soc_alignment",  to: "store_fact_wages",       type: EDGE_TYPES.REQUIRED },
    { from: "gate_soc_alignment",  to: "store_fact_proj",        type: EDGE_TYPES.REQUIRED },
    { from: "gate_soc_alignment",  to: "store_bridges",          type: EDGE_TYPES.REQUIRED },
    { from: "gate_soc_alignment",  to: "store_dim_cpi",          type: EDGE_TYPES.REQUIRED },
    { from: "gate_soc_alignment",  to: "store_crosswalk",        type: EDGE_TYPES.OPTIONAL },

    /* Core dimension dependencies */
    { from: "store_dim_occupation", to: "store_fact_wages",  type: EDGE_TYPES.REQUIRED, condition: "FK: soc_code" },
    { from: "store_dim_occupation", to: "store_fact_proj",   type: EDGE_TYPES.REQUIRED, condition: "FK: soc_code" },
    { from: "store_dim_occupation", to: "store_bridges",     type: EDGE_TYPES.REQUIRED, condition: "FK: soc_code" },
    { from: "store_dim_geography",  to: "store_fact_wages",  type: EDGE_TYPES.REQUIRED, condition: "FK: geo_code" },

    /* Core → Time-Series */
    { from: "store_fact_wages",  to: "proc_ts_observations",  type: EDGE_TYPES.REQUIRED },
    { from: "store_dim_occupation", to: "proc_ts_metrics",    type: EDGE_TYPES.REQUIRED },
    { from: "store_dim_cpi",     to: "proc_ts_cpi_deflation", type: EDGE_TYPES.REQUIRED, condition: "CPI available" },
    { from: "store_crosswalk",   to: "proc_ts_comparable",    type: EDGE_TYPES.CONDITIONAL, condition: "1:1 mappings for wages" },
    { from: "proc_ts_metrics",      to: "proc_ts_periods",       type: EDGE_TYPES.REQUIRED },
    { from: "proc_ts_periods",      to: "proc_ts_observations",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_ts_observations", to: "proc_ts_cpi_deflation", type: EDGE_TYPES.CONDITIONAL, condition: "Nominal → real wages" },
    { from: "proc_ts_observations", to: "proc_ts_derived",       type: EDGE_TYPES.DERIVED },
    { from: "proc_ts_cpi_deflation", to: "proc_ts_derived",     type: EDGE_TYPES.DERIVED },
    { from: "proc_ts_comparable",   to: "proc_ts_observations",  type: EDGE_TYPES.CONDITIONAL, condition: "Comparable history mode" },

    /* Time-Series → Marts */
    { from: "proc_ts_derived",       to: "store_mart_trend",     type: EDGE_TYPES.DERIVED },
    { from: "proc_ts_derived",       to: "store_mart_geo_gap",   type: EDGE_TYPES.DERIVED },
    { from: "proc_ts_derived",       to: "store_mart_rank",      type: EDGE_TYPES.DERIVED },

    /* Core → Marts */
    { from: "store_dim_occupation",  to: "store_mart_summary",       type: EDGE_TYPES.REQUIRED },
    { from: "store_fact_wages",      to: "store_mart_wages_geo",     type: EDGE_TYPES.REQUIRED },
    { from: "store_bridges",         to: "store_mart_skill_profile", type: EDGE_TYPES.REQUIRED },
    { from: "store_bridges",         to: "store_mart_similarity",    type: EDGE_TYPES.REQUIRED },

    /* Marts → Interface Pages */
    { from: "store_mart_summary",       to: "iface_search",          type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_summary",       to: "iface_hierarchy",       type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_summary",       to: "iface_occupation",      type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_wages_geo",     to: "iface_wages",           type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_skill_profile", to: "iface_occupation",      type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_trend",         to: "iface_trend_explorer",  type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_trend",         to: "iface_occ_compare",     type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_geo_gap",       to: "iface_geo_compare",     type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_rank",          to: "iface_movers",          type: EDGE_TYPES.REQUIRED },
    { from: "store_dim_cpi",            to: "iface_cpi",             type: EDGE_TYPES.REQUIRED },
    { from: "store_mart_similarity",    to: "iface_occupation",      type: EDGE_TYPES.OPTIONAL, condition: "Similar occupations tab" },

    /* Interface → Deployment */
    { from: "iface_search",         to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_hierarchy",      to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_occupation",     to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_wages",          to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_trend_explorer", to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_occ_compare",    to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_geo_compare",    to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_movers",         to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_cpi",            to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_methodology",    to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_lessons",        to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "iface_pipeline",       to: "proc_build_static",  type: EDGE_TYPES.REQUIRED },
    { from: "proc_build_static",    to: "proc_fetch_shim",    type: EDGE_TYPES.REQUIRED },
    { from: "proc_fetch_shim",      to: "proc_deploy",        type: EDGE_TYPES.REQUIRED },

    /* CLI orchestration */
    { from: "proc_cli", to: "proc_download_mgr", type: EDGE_TYPES.REQUIRED, condition: "run-all" },
    { from: "proc_cli", to: "proc_ts_metrics",   type: EDGE_TYPES.REQUIRED, condition: "timeseries-refresh" },
    { from: "proc_cli", to: "proc_health",       type: EDGE_TYPES.OPTIONAL, condition: "status" }
];

/* --- PE1-15: Lesson Anchor Mappings --- */
var LESSON_ANCHORS = {
    "federal-data":         ["src_soc", "src_oews", "src_onet", "src_projections", "src_cpi", "src_crosswalk"],
    "dimensional-modeling": ["store_dim_occupation", "store_dim_geography", "store_dim_descriptors", "store_fact_wages", "store_bridges"],
    "multi-vintage":        ["proc_ts_observations", "proc_ts_comparable", "store_crosswalk"],
    "data-quality":         ["gate_schema_drift", "gate_referential", "gate_grain", "gate_null_semantics"],
    "time-series":          ["proc_ts_metrics", "proc_ts_periods", "proc_ts_observations", "proc_ts_derived"],
    "idempotent-pipelines": ["gate_grain", "proc_download_mgr", "proc_run_manifest"],
    "static-site":          ["proc_build_static", "proc_fetch_shim", "proc_deploy"],
    "testing-deployment":   ["proc_health", "proc_deploy", "proc_cli"],
    "similarity-algorithms": ["store_mart_similarity", "store_bridges"],
    "thread-safety":        ["proc_download_mgr", "proc_ts_observations"],
    "multi-vintage-queries": ["proc_ts_observations", "proc_ts_comparable", "store_mart_trend"],
    "ui-data-alignment":    ["iface_trend_explorer", "iface_occupation", "iface_wages"],
    "schema-drift":         ["gate_schema_drift", "proc_parse_soc", "proc_parse_oews"],
    "inflation-adjustment": ["src_cpi", "proc_ts_cpi_deflation", "store_dim_cpi"],
    "taxonomy-evolution":   ["src_crosswalk", "store_crosswalk", "proc_ts_comparable"],
    "government-apis":      ["proc_download_mgr", "proc_browser_headers", "src_oews", "src_cpi"],
    "derived-metrics":      ["proc_ts_derived", "store_mart_trend", "store_mart_rank"],
    "outlier-interpretation": ["store_mart_rank", "iface_movers"],
    "geography-pitfalls":   ["store_dim_geography", "store_mart_geo_gap", "iface_geo_compare"],
    "fetch-shim":           ["proc_fetch_shim", "proc_build_static", "proc_deploy"]
};

/* --- Guided Mode Sequences (PE9 data, defined here for data-driven design) --- */
var GUIDED_MODES = [
    {
        id: "follow-data",
        name: "Follow the Data",
        description: "Trace how federal data flows from source acquisition through the warehouse to visible web pages.",
        steps: [
            { nodeId: "src_oews",            annotation: "Data begins at federal sources like the OEWS survey, published annually by BLS." },
            { nodeId: "proc_download_mgr",   annotation: "The download manager fetches source artifacts using browser-like headers to bypass BLS blocking." },
            { nodeId: "store_raw_oews",      annotation: "Raw files land in immutable storage — never overwritten, ensuring reproducibility." },
            { nodeId: "proc_parse_oews",     annotation: "The OEWS parser normalizes UPPERCASE column names and creates standardized staging tables." },
            { nodeId: "gate_schema_drift",   annotation: "Validation gates check for schema changes, referential integrity, and grain uniqueness." },
            { nodeId: "store_fact_wages",    annotation: "Validated data loads into core facts: employment counts and wage measures by occupation and geography." },
            { nodeId: "store_mart_trend",    annotation: "Mart views aggregate core facts into analyst-ready shapes for the web layer." },
            { nodeId: "iface_trend_explorer", annotation: "Web pages fetch from mart-backed APIs to show interactive charts and comparisons." }
        ]
    },
    {
        id: "what-breaks",
        name: "What Can Break",
        description: "See where validation gates enforce data quality and what happens when things go wrong.",
        steps: [
            { nodeId: "gate_schema_drift",   annotation: "Schema drift detection blocks publication if source columns change unexpectedly." },
            { nodeId: "gate_soc_alignment",  annotation: "5 NEM 2024 occupation codes don't map to SOC 2018 — these rows are silently excluded." },
            { nodeId: "gate_null_semantics", annotation: "Suppressed OEWS values must remain null. Imputation would silently corrupt analysis." },
            { nodeId: "gate_referential",    annotation: "Every fact and bridge row must point to an existing dimension. Orphan references are rejected." },
            { nodeId: "gate_grain",          annotation: "Duplicate business keys would break idempotency. Re-running must not create duplicates." },
            { nodeId: "gate_temporal",       annotation: "Version monotonicity and period ordering prevent time-travel anomalies in the data." }
        ]
    },
    {
        id: "time-series",
        name: "Time-Series Path",
        description: "Follow the time-series enrichment path: multi-vintage loading, CPI deflation, derived series, and trend pages.",
        steps: [
            { nodeId: "store_fact_wages",      annotation: "Multi-vintage OEWS data (2021-2023) provides the base for time-series analysis." },
            { nodeId: "proc_ts_metrics",       annotation: "Six base metrics are defined: employment count, mean/median wage, projections, change, percent change." },
            { nodeId: "proc_ts_observations",  annotation: "OEWS observations are aggregated with comparable and as-published modes." },
            { nodeId: "proc_ts_cpi_deflation", annotation: "CPI-U deflation converts nominal wages to real (2023 dollars). Formula: real = nominal * (CPI_2023 / CPI_year)." },
            { nodeId: "proc_ts_comparable",    annotation: "SOC crosswalk enables comparable history across taxonomy revisions. Only 1:1 mappings for wages." },
            { nodeId: "proc_ts_derived",       annotation: "Derived series compute year-over-year changes and percent changes." },
            { nodeId: "store_mart_trend",      annotation: "Trend marts power the web-facing time-series views." },
            { nodeId: "iface_trend_explorer",  annotation: "The Trend Explorer shows interactive time-series charts per occupation." }
        ]
    },
    {
        id: "query-proof",
        name: "From Query to Proof",
        description: "Start from a visible page and trace backward to prove where the data comes from.",
        steps: [
            { nodeId: "iface_movers",          annotation: "The Ranked Movers page shows top gainers and losers. Where does this data come from?" },
            { nodeId: "store_mart_rank",       annotation: "The rank_change mart computes year-over-year ranking changes from time-series observations." },
            { nodeId: "proc_ts_derived",       annotation: "Derived series (YoY change, percent change) are computed from base observations." },
            { nodeId: "proc_ts_observations",  annotation: "Base observations come from multi-vintage OEWS data, loaded with comparability tracking." },
            { nodeId: "store_fact_wages",      annotation: "The core fact table stores validated employment and wage measures." },
            { nodeId: "gate_soc_alignment",    annotation: "Validation confirmed every occupation code maps to dim_occupation before loading." },
            { nodeId: "proc_parse_oews",       annotation: "The OEWS parser normalized the raw XLSX into standardized staging tables." },
            { nodeId: "src_oews",              annotation: "The original data is the BLS OEWS survey — the authoritative source for occupation wages." }
        ]
    }
];

/* --- Exported Graph Object --- */
var PIPELINE_GRAPH = {
    nodeTypes: NODE_TYPES,
    edgeTypes: EDGE_TYPES,
    lanes: LANES,
    nodes: GRAPH_NODES,
    edges: GRAPH_EDGES,
    lessonAnchors: LESSON_ANCHORS,
    guidedModes: GUIDED_MODES
};
