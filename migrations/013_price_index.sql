-- Migration 013: BLS CPI-U price index — staging, dimension, and fact tables.

-- Staging table for CPI data
CREATE TABLE IF NOT EXISTS stage__bls__cpi (
    series_id         TEXT NOT NULL,
    year              INTEGER NOT NULL,
    period            TEXT NOT NULL,
    value             DOUBLE NOT NULL,
    source_release_id TEXT NOT NULL,
    parser_version    TEXT NOT NULL
);

-- Dimension table
CREATE SEQUENCE IF NOT EXISTS seq_price_index_key START 1;
CREATE TABLE IF NOT EXISTS dim_price_index (
    price_index_key   INTEGER PRIMARY KEY DEFAULT nextval('seq_price_index_key'),
    series_id         TEXT NOT NULL,
    series_name       TEXT NOT NULL,
    base_period       TEXT,
    seasonally_adjusted BOOLEAN DEFAULT TRUE,
    source_release_id TEXT NOT NULL
);

-- Fact table for CPI observations
CREATE SEQUENCE IF NOT EXISTS seq_price_index_obs_key START 1;
CREATE TABLE IF NOT EXISTS fact_price_index_observation (
    observation_key   INTEGER DEFAULT nextval('seq_price_index_obs_key'),
    price_index_key   INTEGER NOT NULL,
    period_key        INTEGER NOT NULL,
    index_value       DOUBLE NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);
