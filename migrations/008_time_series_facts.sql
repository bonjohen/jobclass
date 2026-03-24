-- Migration 008: Time-series observation and derived-series fact tables (Phase TS2, TS5)

-- ============================================================
-- Base time-series observation fact
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS seq_observation_key START 1;

CREATE TABLE IF NOT EXISTS fact_time_series_observation (
    observation_key     INTEGER PRIMARY KEY DEFAULT nextval('seq_observation_key'),
    metric_key          INTEGER NOT NULL,
    occupation_key      INTEGER NOT NULL,
    geography_key       INTEGER NOT NULL,
    period_key          INTEGER NOT NULL,
    source_release_id   TEXT NOT NULL,
    comparability_mode  TEXT NOT NULL DEFAULT 'as_published',
    observed_value      DOUBLE,
    suppression_flag    BOOLEAN NOT NULL DEFAULT false,
    run_id              TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_ts_obs_grain
    ON fact_time_series_observation (
        metric_key, occupation_key, geography_key, period_key,
        source_release_id, comparability_mode
    );

-- ============================================================
-- Derived-series fact
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS seq_derived_key START 1;

CREATE TABLE IF NOT EXISTS fact_derived_series (
    derived_key         INTEGER PRIMARY KEY DEFAULT nextval('seq_derived_key'),
    metric_key          INTEGER NOT NULL,
    base_metric_key     INTEGER NOT NULL,
    occupation_key      INTEGER NOT NULL,
    geography_key       INTEGER NOT NULL,
    period_key          INTEGER NOT NULL,
    comparability_mode  TEXT NOT NULL DEFAULT 'as_published',
    derived_value       DOUBLE,
    derivation_method   TEXT NOT NULL,
    run_id              TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_derived_grain
    ON fact_derived_series (
        metric_key, base_metric_key, occupation_key, geography_key,
        period_key, comparability_mode
    );
