-- Migration 006: Employment Projections staging and fact tables (Phase 10)

-- ============================================================
-- Staging table
-- ============================================================

CREATE TABLE IF NOT EXISTS stage__bls__employment_projections (
    projection_cycle    TEXT NOT NULL,
    occupation_code     TEXT NOT NULL,
    occupation_title    TEXT,
    base_year           INTEGER NOT NULL,
    projection_year     INTEGER NOT NULL,
    employment_base     INTEGER,
    employment_projected INTEGER,
    employment_change_abs INTEGER,
    employment_change_pct DOUBLE,
    annual_openings     INTEGER,
    education_category  TEXT,
    training_category   TEXT,
    work_experience_category TEXT,
    source_release_id   TEXT NOT NULL,
    parser_version      TEXT NOT NULL
);

-- ============================================================
-- Fact table
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS seq_fact_proj_key START 1;

CREATE TABLE IF NOT EXISTS fact_occupation_projections (
    fact_id                INTEGER PRIMARY KEY DEFAULT nextval('seq_fact_proj_key'),
    projection_cycle       TEXT NOT NULL,
    occupation_key         INTEGER NOT NULL,
    base_year              INTEGER NOT NULL,
    projection_year        INTEGER NOT NULL,
    employment_base        INTEGER,
    employment_projected   INTEGER,
    employment_change_abs  INTEGER,
    employment_change_pct  DOUBLE,
    annual_openings        INTEGER,
    education_category     TEXT,
    training_category      TEXT,
    work_experience_category TEXT,
    source_release_id      TEXT NOT NULL,
    load_timestamp         TIMESTAMPTZ NOT NULL DEFAULT now()
);
