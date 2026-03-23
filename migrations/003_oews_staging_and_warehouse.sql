-- Phase 4: OEWS staging tables, dim_geography, dim_industry, fact_occupation_employment_wages

-- Staging tables (same schema for national and state)
CREATE TABLE IF NOT EXISTS stage__bls__oews_national (
    area_type           TEXT NOT NULL,
    area_code           TEXT NOT NULL,
    area_title          TEXT,
    naics_code          TEXT,
    naics_title         TEXT,
    ownership_code      TEXT,
    occupation_code     TEXT NOT NULL,
    occupation_title    TEXT,
    occupation_group    TEXT,
    employment_count    INTEGER,
    employment_rse      DOUBLE,
    jobs_per_1000       DOUBLE,
    location_quotient   DOUBLE,
    mean_hourly_wage    DOUBLE,
    mean_annual_wage    DOUBLE,
    mean_wage_rse       DOUBLE,
    median_hourly_wage  DOUBLE,
    median_annual_wage  DOUBLE,
    p10_hourly_wage     DOUBLE,
    p25_hourly_wage     DOUBLE,
    p75_hourly_wage     DOUBLE,
    p90_hourly_wage     DOUBLE,
    p10_annual_wage     DOUBLE,
    p25_annual_wage     DOUBLE,
    p75_annual_wage     DOUBLE,
    p90_annual_wage     DOUBLE,
    source_release_id   TEXT NOT NULL,
    parser_version      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stage__bls__oews_state (
    area_type           TEXT NOT NULL,
    area_code           TEXT NOT NULL,
    area_title          TEXT,
    naics_code          TEXT,
    naics_title         TEXT,
    ownership_code      TEXT,
    occupation_code     TEXT NOT NULL,
    occupation_title    TEXT,
    occupation_group    TEXT,
    employment_count    INTEGER,
    employment_rse      DOUBLE,
    jobs_per_1000       DOUBLE,
    location_quotient   DOUBLE,
    mean_hourly_wage    DOUBLE,
    mean_annual_wage    DOUBLE,
    mean_wage_rse       DOUBLE,
    median_hourly_wage  DOUBLE,
    median_annual_wage  DOUBLE,
    p10_hourly_wage     DOUBLE,
    p25_hourly_wage     DOUBLE,
    p75_hourly_wage     DOUBLE,
    p90_hourly_wage     DOUBLE,
    p10_annual_wage     DOUBLE,
    p25_annual_wage     DOUBLE,
    p75_annual_wage     DOUBLE,
    p90_annual_wage     DOUBLE,
    source_release_id   TEXT NOT NULL,
    parser_version      TEXT NOT NULL
);

-- Core dimension: geography
CREATE TABLE IF NOT EXISTS dim_geography (
    geography_key       INTEGER PRIMARY KEY,
    geo_type            TEXT NOT NULL,
    geo_code            TEXT NOT NULL,
    geo_name            TEXT,
    state_fips          TEXT,
    county_fips         TEXT,
    msa_code            TEXT,
    is_cross_state      BOOLEAN,
    effective_start_date TEXT,
    effective_end_date  TEXT,
    is_current          BOOLEAN NOT NULL DEFAULT true,
    source_release_id   TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_geography_bk
    ON dim_geography (geo_type, geo_code, source_release_id);

CREATE SEQUENCE IF NOT EXISTS seq_geography_key START 1;

-- Core dimension: industry
CREATE TABLE IF NOT EXISTS dim_industry (
    industry_key        INTEGER PRIMARY KEY,
    naics_code          TEXT NOT NULL,
    industry_title      TEXT,
    industry_level      INTEGER,
    parent_naics_code   TEXT,
    naics_version       TEXT NOT NULL,
    effective_start_date TEXT,
    effective_end_date  TEXT,
    is_current          BOOLEAN NOT NULL DEFAULT true
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_industry_bk
    ON dim_industry (naics_code, naics_version);

CREATE SEQUENCE IF NOT EXISTS seq_industry_key START 1;

-- Core fact table
CREATE TABLE IF NOT EXISTS fact_occupation_employment_wages (
    fact_id             INTEGER PRIMARY KEY,
    reference_period    TEXT NOT NULL,
    estimate_year       INTEGER,
    geography_key       INTEGER NOT NULL,
    industry_key        INTEGER,
    ownership_code      TEXT,
    occupation_key      INTEGER NOT NULL,
    employment_count    INTEGER,
    employment_rse      DOUBLE,
    jobs_per_1000       DOUBLE,
    location_quotient   DOUBLE,
    mean_hourly_wage    DOUBLE,
    mean_annual_wage    DOUBLE,
    median_hourly_wage  DOUBLE,
    median_annual_wage  DOUBLE,
    p10_hourly_wage     DOUBLE,
    p25_hourly_wage     DOUBLE,
    p75_hourly_wage     DOUBLE,
    p90_hourly_wage     DOUBLE,
    source_dataset      TEXT NOT NULL,
    source_release_id   TEXT NOT NULL,
    load_timestamp      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS seq_fact_oew_key START 1;
