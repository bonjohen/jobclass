-- Migration 015: CPI domain expansion — dimensions, bridges, facts, and staging tables
-- for the full CPI analytical domain (members, hierarchy, areas, series variants,
-- observations, relative importance, average prices, and revision vintages).

-- ============================================================================
-- STAGING TABLES
-- ============================================================================

-- Staging: CPI series metadata (decomposed series IDs)
CREATE TABLE IF NOT EXISTS stage__bls__cpi_series (
    series_id             TEXT NOT NULL,
    index_family          TEXT NOT NULL,
    seasonal_adjustment   TEXT NOT NULL,
    periodicity           TEXT NOT NULL,
    area_code             TEXT NOT NULL,
    item_code             TEXT NOT NULL,
    source_release_id     TEXT NOT NULL,
    parser_version        TEXT NOT NULL
);

-- Staging: CPI item hierarchy (BLS aggregation tree)
CREATE TABLE IF NOT EXISTS stage__bls__cpi_item_hierarchy (
    item_code             TEXT NOT NULL,
    item_name             TEXT NOT NULL,
    hierarchy_level       TEXT NOT NULL,
    parent_item_code      TEXT,
    sort_sequence         INTEGER,
    selectable            BOOLEAN,
    source_release_id     TEXT NOT NULL,
    parser_version        TEXT NOT NULL
);

-- Staging: CPI publication level (Appendix 7 — items by area type)
CREATE TABLE IF NOT EXISTS stage__bls__cpi_publication_level (
    item_code             TEXT NOT NULL,
    item_name             TEXT NOT NULL,
    area_type             TEXT NOT NULL,
    published             BOOLEAN NOT NULL,
    source_release_id     TEXT NOT NULL,
    parser_version        TEXT NOT NULL
);

-- Staging: CPI relative importance
CREATE TABLE IF NOT EXISTS stage__bls__cpi_relative_importance (
    item_code             TEXT NOT NULL,
    area_code             TEXT NOT NULL,
    reference_period      TEXT NOT NULL,
    relative_importance   DOUBLE NOT NULL,
    source_release_id     TEXT NOT NULL,
    parser_version        TEXT NOT NULL
);

-- Staging: CPI average prices
CREATE TABLE IF NOT EXISTS stage__bls__cpi_average_price (
    item_code             TEXT NOT NULL,
    area_code             TEXT NOT NULL,
    year                  INTEGER NOT NULL,
    period                TEXT NOT NULL,
    average_price         DOUBLE NOT NULL,
    unit_description      TEXT,
    source_release_id     TEXT NOT NULL,
    parser_version        TEXT NOT NULL
);

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- dim_cpi_member: browsable CPI items (hierarchy nodes + special aggregates)
CREATE SEQUENCE IF NOT EXISTS seq_cpi_member_key START 1;
CREATE TABLE IF NOT EXISTS dim_cpi_member (
    member_key            INTEGER PRIMARY KEY DEFAULT nextval('seq_cpi_member_key'),
    member_code           TEXT NOT NULL,
    title                 TEXT NOT NULL,
    hierarchy_level       TEXT,
    semantic_role         TEXT NOT NULL,
    is_cross_cutting      BOOLEAN NOT NULL DEFAULT FALSE,
    has_average_price     BOOLEAN NOT NULL DEFAULT FALSE,
    has_relative_importance BOOLEAN NOT NULL DEFAULT FALSE,
    publication_depth     TEXT,
    source_version        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_cpi_member_bk
    ON dim_cpi_member (member_code, source_version);

-- dim_cpi_area: geographic areas for CPI publication
CREATE SEQUENCE IF NOT EXISTS seq_cpi_area_key START 1;
CREATE TABLE IF NOT EXISTS dim_cpi_area (
    area_key              INTEGER PRIMARY KEY DEFAULT nextval('seq_cpi_area_key'),
    area_code             TEXT NOT NULL,
    area_title            TEXT NOT NULL,
    area_type             TEXT NOT NULL,
    publication_frequency TEXT NOT NULL,
    source_version        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_cpi_area_bk
    ON dim_cpi_area (area_code, source_version);

-- dim_cpi_series_variant: one member × area × index family × adjustment × periodicity
CREATE SEQUENCE IF NOT EXISTS seq_cpi_variant_key START 1;
CREATE TABLE IF NOT EXISTS dim_cpi_series_variant (
    variant_key           INTEGER PRIMARY KEY DEFAULT nextval('seq_cpi_variant_key'),
    series_id             TEXT NOT NULL,
    index_family          TEXT NOT NULL,
    seasonal_adjustment   TEXT NOT NULL,
    periodicity           TEXT NOT NULL,
    area_code             TEXT NOT NULL,
    item_code             TEXT NOT NULL,
    member_key            INTEGER,
    area_key              INTEGER,
    source_version        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_cpi_variant_bk
    ON dim_cpi_series_variant (series_id, source_version);

-- ============================================================================
-- BRIDGE TABLES
-- ============================================================================

-- bridge_cpi_member_hierarchy: formal BLS item tree edges
CREATE TABLE IF NOT EXISTS bridge_cpi_member_hierarchy (
    parent_member_key     INTEGER NOT NULL,
    child_member_key      INTEGER NOT NULL,
    hierarchy_depth       INTEGER NOT NULL DEFAULT 1,
    source_version        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_cpi_member_hierarchy
    ON bridge_cpi_member_hierarchy (parent_member_key, child_member_key, source_version);

-- bridge_cpi_member_relation: cross-cutting analytical relationships
CREATE TABLE IF NOT EXISTS bridge_cpi_member_relation (
    member_key_a          INTEGER NOT NULL,
    member_key_b          INTEGER NOT NULL,
    relation_type         TEXT NOT NULL,
    description           TEXT,
    source_version        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_cpi_member_relation
    ON bridge_cpi_member_relation (member_key_a, member_key_b, relation_type, source_version);

-- bridge_cpi_area_hierarchy: area tree edges (national → region → division → metro)
CREATE TABLE IF NOT EXISTS bridge_cpi_area_hierarchy (
    parent_area_key       INTEGER NOT NULL,
    child_area_key        INTEGER NOT NULL,
    source_version        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_cpi_area_hierarchy
    ON bridge_cpi_area_hierarchy (parent_area_key, child_area_key, source_version);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- fact_cpi_observation: base index observations (grain: variant × period)
CREATE TABLE IF NOT EXISTS fact_cpi_observation (
    member_key            INTEGER NOT NULL,
    area_key              INTEGER NOT NULL,
    variant_key           INTEGER NOT NULL,
    time_period_key       INTEGER NOT NULL,
    index_value           DOUBLE NOT NULL,
    percent_change_month  DOUBLE,
    percent_change_year   DOUBLE,
    source_release_id     TEXT NOT NULL,
    load_timestamp        TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_fact_cpi_observation_grain
    ON fact_cpi_observation (variant_key, time_period_key);

-- fact_cpi_relative_importance: expenditure-share weights (grain: member × area × period)
CREATE TABLE IF NOT EXISTS fact_cpi_relative_importance (
    member_key            INTEGER NOT NULL,
    area_key              INTEGER NOT NULL,
    reference_period      TEXT NOT NULL,
    relative_importance_value DOUBLE NOT NULL,
    source_release_id     TEXT NOT NULL,
    load_timestamp        TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_fact_cpi_importance_grain
    ON fact_cpi_relative_importance (member_key, area_key, reference_period);

-- fact_cpi_average_price: published average prices for food/fuel/utility items
-- (grain: member × area × period)
CREATE TABLE IF NOT EXISTS fact_cpi_average_price (
    member_key            INTEGER NOT NULL,
    area_key              INTEGER NOT NULL,
    time_period_key       INTEGER NOT NULL,
    average_price         DOUBLE NOT NULL,
    unit_description      TEXT,
    source_release_id     TEXT NOT NULL,
    load_timestamp        TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_fact_cpi_avg_price_grain
    ON fact_cpi_average_price (member_key, area_key, time_period_key);

-- fact_cpi_revision_vintage: C-CPI-U preliminary/revised values
-- (grain: member × area × period × vintage)
CREATE TABLE IF NOT EXISTS fact_cpi_revision_vintage (
    member_key            INTEGER NOT NULL,
    area_key              INTEGER NOT NULL,
    time_period_key       INTEGER NOT NULL,
    vintage_label         TEXT NOT NULL,
    index_value           DOUBLE NOT NULL,
    is_preliminary        BOOLEAN NOT NULL DEFAULT TRUE,
    revision_date         DATE,
    source_release_id     TEXT NOT NULL,
    load_timestamp        TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_fact_cpi_vintage_grain
    ON fact_cpi_revision_vintage (member_key, area_key, time_period_key, vintage_label);
