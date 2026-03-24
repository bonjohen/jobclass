-- Migration 012: O*NET Technology Skills — staging, dimension, and bridge tables.

-- Staging table (different from descriptors: commodity-based, no scale/value)
CREATE TABLE IF NOT EXISTS stage__onet__technology_skills (
    occupation_code   TEXT NOT NULL,
    t2_type           TEXT NOT NULL,
    example_name      TEXT NOT NULL,
    commodity_code    TEXT,
    commodity_title   TEXT,
    hot_technology    BOOLEAN,
    date              TEXT,
    domain_source     TEXT,
    source_release_id TEXT NOT NULL,
    parser_version    TEXT NOT NULL
);

-- Dimension table
CREATE SEQUENCE IF NOT EXISTS seq_technology_key START 1;
CREATE TABLE IF NOT EXISTS dim_technology (
    technology_key    INTEGER PRIMARY KEY DEFAULT nextval('seq_technology_key'),
    commodity_code    TEXT,
    commodity_title   TEXT,
    t2_type           TEXT NOT NULL,
    example_name      TEXT NOT NULL,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

-- Bridge table (occupation ↔ technology — binary association)
CREATE TABLE IF NOT EXISTS bridge_occupation_technology (
    occupation_key    INTEGER NOT NULL,
    technology_key    INTEGER NOT NULL,
    hot_technology    BOOLEAN,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);
