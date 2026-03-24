-- Migration 007: Time-series dimension tables (Phase TS1)
-- dim_metric: conformed metric catalog
-- dim_time_period: time-period dimension for annual observations

-- ============================================================
-- Metric catalog
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS seq_metric_key START 1;

CREATE TABLE IF NOT EXISTS dim_metric (
    metric_key          INTEGER PRIMARY KEY DEFAULT nextval('seq_metric_key'),
    metric_name         TEXT NOT NULL UNIQUE,
    units               TEXT NOT NULL,
    display_format      TEXT NOT NULL DEFAULT '#,##0',
    comparability_constraint TEXT,
    derivation_type     TEXT NOT NULL DEFAULT 'base',
    description         TEXT,
    requires_comparable_input BOOLEAN NOT NULL DEFAULT false
);

-- ============================================================
-- Time-period dimension
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS seq_period_key START 1;

CREATE TABLE IF NOT EXISTS dim_time_period (
    period_key          INTEGER PRIMARY KEY DEFAULT nextval('seq_period_key'),
    period_type         TEXT NOT NULL DEFAULT 'annual',
    year                INTEGER NOT NULL,
    quarter             INTEGER,
    period_start_date   DATE NOT NULL,
    period_end_date     DATE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_time_period_bk
    ON dim_time_period (period_type, year, quarter);
