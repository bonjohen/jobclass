-- Migration 009: Time-series reporting mart views (Phase TS8)

-- ============================================================
-- mart_occupation_trend_series
-- ============================================================
CREATE OR REPLACE VIEW mart_occupation_trend_series AS
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    m.metric_key,
    m.metric_name,
    m.units,
    m.derivation_type,
    g.geography_key,
    g.geo_type,
    g.geo_code,
    g.geo_name,
    tp.period_key,
    tp.year,
    tp.period_type,
    obs.observed_value,
    obs.comparability_mode,
    obs.source_release_id,
    obs.suppression_flag,
    d_yoy.derived_value AS yoy_change,
    d_pct.derived_value AS yoy_pct_change,
    d_avg.derived_value AS rolling_avg
FROM fact_time_series_observation obs
JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
JOIN dim_metric m ON obs.metric_key = m.metric_key
JOIN dim_geography g ON obs.geography_key = g.geography_key
JOIN dim_time_period tp ON obs.period_key = tp.period_key
LEFT JOIN fact_derived_series d_yoy
  ON d_yoy.base_metric_key = obs.metric_key
  AND d_yoy.occupation_key = obs.occupation_key
  AND d_yoy.geography_key = obs.geography_key
  AND d_yoy.period_key = obs.period_key
  AND d_yoy.comparability_mode = obs.comparability_mode
  AND d_yoy.derivation_method = 'yoy_absolute_change'
LEFT JOIN fact_derived_series d_pct
  ON d_pct.base_metric_key = obs.metric_key
  AND d_pct.occupation_key = obs.occupation_key
  AND d_pct.geography_key = obs.geography_key
  AND d_pct.period_key = obs.period_key
  AND d_pct.comparability_mode = obs.comparability_mode
  AND d_pct.derivation_method = 'yoy_percent_change'
LEFT JOIN fact_derived_series d_avg
  ON d_avg.base_metric_key = obs.metric_key
  AND d_avg.occupation_key = obs.occupation_key
  AND d_avg.geography_key = obs.geography_key
  AND d_avg.period_key = obs.period_key
  AND d_avg.comparability_mode = obs.comparability_mode
  AND d_avg.derivation_method = 'rolling_avg_3yr'
WHERE o.is_current = true;


-- ============================================================
-- mart_occupation_geography_gap_series
-- ============================================================
CREATE OR REPLACE VIEW mart_occupation_geography_gap_series AS
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    m.metric_key,
    m.metric_name,
    g.geography_key,
    g.geo_type,
    g.geo_code,
    g.geo_name AS state_name,
    tp.period_key,
    tp.year,
    state_obs.observed_value AS state_value,
    nat_obs.observed_value AS national_value,
    d.derived_value AS gap,
    state_obs.comparability_mode,
    state_obs.source_release_id
FROM fact_derived_series d
JOIN dim_metric m ON d.base_metric_key = m.metric_key
JOIN dim_occupation o ON d.occupation_key = o.occupation_key
JOIN dim_geography g ON d.geography_key = g.geography_key
JOIN dim_time_period tp ON d.period_key = tp.period_key
JOIN fact_time_series_observation state_obs
  ON state_obs.metric_key = d.base_metric_key
  AND state_obs.occupation_key = d.occupation_key
  AND state_obs.geography_key = d.geography_key
  AND state_obs.period_key = d.period_key
  AND state_obs.comparability_mode = d.comparability_mode
JOIN dim_geography g_nat ON g_nat.geo_type = 'national'
JOIN fact_time_series_observation nat_obs
  ON nat_obs.metric_key = d.base_metric_key
  AND nat_obs.occupation_key = d.occupation_key
  AND nat_obs.geography_key = g_nat.geography_key
  AND nat_obs.period_key = d.period_key
  AND nat_obs.comparability_mode = d.comparability_mode
WHERE d.derivation_method = 'state_vs_national_gap'
  AND g.geo_type = 'state'
  AND o.is_current = true;


-- ============================================================
-- mart_occupation_rank_change
-- ============================================================
CREATE OR REPLACE VIEW mart_occupation_rank_change AS
WITH ranked AS (
    SELECT
        obs.occupation_key,
        obs.geography_key,
        obs.metric_key,
        obs.period_key,
        obs.comparability_mode,
        tp.year,
        RANK() OVER (
            PARTITION BY obs.geography_key, obs.metric_key, obs.period_key, obs.comparability_mode
            ORDER BY obs.observed_value DESC
        ) AS rnk
    FROM fact_time_series_observation obs
    JOIN dim_time_period tp ON obs.period_key = tp.period_key
    JOIN dim_metric m ON obs.metric_key = m.metric_key
    WHERE obs.comparability_mode = 'comparable'
      AND obs.observed_value IS NOT NULL
      AND m.derivation_type = 'base'
      AND m.comparability_constraint = 'same_soc_version'
)
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    m.metric_key,
    m.metric_name,
    g.geography_key,
    g.geo_type,
    g.geo_name,
    tp.period_key,
    tp.year,
    curr.rnk AS rank,
    prev.rnk AS prior_rank,
    prev.rnk - curr.rnk AS rank_delta,
    curr.comparability_mode
FROM ranked curr
JOIN ranked prev
  ON prev.occupation_key = curr.occupation_key
  AND prev.geography_key = curr.geography_key
  AND prev.metric_key = curr.metric_key
  AND prev.comparability_mode = curr.comparability_mode
  AND prev.year = curr.year - 1
JOIN dim_occupation o ON curr.occupation_key = o.occupation_key
JOIN dim_metric m ON curr.metric_key = m.metric_key
JOIN dim_geography g ON curr.geography_key = g.geography_key
JOIN dim_time_period tp ON curr.period_key = tp.period_key
WHERE o.is_current = true;


-- ============================================================
-- mart_occupation_projection_context
-- ============================================================
CREATE OR REPLACE VIEW mart_occupation_projection_context AS
WITH last_observed AS (
    SELECT
        obs.occupation_key,
        obs.geography_key,
        m.metric_key,
        m.metric_name,
        obs.observed_value AS last_observed_value,
        tp.year AS last_observed_year,
        ROW_NUMBER() OVER (
            PARTITION BY obs.occupation_key, obs.geography_key, obs.metric_key
            ORDER BY tp.year DESC
        ) AS rn
    FROM fact_time_series_observation obs
    JOIN dim_metric m ON obs.metric_key = m.metric_key
    JOIN dim_time_period tp ON obs.period_key = tp.period_key
    WHERE m.metric_name IN ('employment_count')
      AND obs.comparability_mode = 'as_published'
      AND obs.observed_value IS NOT NULL
),
projected AS (
    SELECT
        obs.occupation_key,
        obs.geography_key,
        obs.observed_value AS projected_value,
        tp.year AS projection_year
    FROM fact_time_series_observation obs
    JOIN dim_metric m ON obs.metric_key = m.metric_key
    JOIN dim_time_period tp ON obs.period_key = tp.period_key
    WHERE m.metric_name = 'projected_employment'
      AND obs.comparability_mode = 'as_published'
      AND obs.observed_value IS NOT NULL
)
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    lo.metric_name,
    lo.last_observed_value,
    lo.last_observed_year,
    p.projected_value,
    p.projection_year,
    p.projected_value - lo.last_observed_value AS projection_gap,
    g.geography_key,
    g.geo_type,
    g.geo_name
FROM last_observed lo
JOIN projected p
  ON p.occupation_key = lo.occupation_key
  AND p.geography_key = lo.geography_key
JOIN dim_occupation o ON lo.occupation_key = o.occupation_key
JOIN dim_geography g ON lo.geography_key = g.geography_key
WHERE lo.rn = 1
  AND o.is_current = true;


-- ============================================================
-- mart_occupation_similarity_trend_overlay
-- ============================================================
CREATE OR REPLACE VIEW mart_occupation_similarity_trend_overlay AS
SELECT
    sim.occupation_key_a AS seed_occupation_key,
    oa.soc_code AS seed_soc_code,
    oa.occupation_title AS seed_title,
    sim.occupation_key_b AS similar_occupation_key,
    ob.soc_code AS similar_soc_code,
    ob.occupation_title AS similar_title,
    sim.jaccard_similarity,
    m.metric_key,
    m.metric_name,
    tp.year,
    seed_obs.observed_value AS seed_value,
    sim_obs.observed_value AS similar_value,
    seed_obs.comparability_mode
FROM occupation_similarity_seeded sim
JOIN fact_time_series_observation seed_obs
  ON seed_obs.occupation_key = sim.occupation_key_a
JOIN fact_time_series_observation sim_obs
  ON sim_obs.occupation_key = sim.occupation_key_b
  AND sim_obs.metric_key = seed_obs.metric_key
  AND sim_obs.geography_key = seed_obs.geography_key
  AND sim_obs.period_key = seed_obs.period_key
  AND sim_obs.comparability_mode = seed_obs.comparability_mode
JOIN dim_occupation oa ON sim.occupation_key_a = oa.occupation_key
JOIN dim_occupation ob ON sim.occupation_key_b = ob.occupation_key
JOIN dim_metric m ON seed_obs.metric_key = m.metric_key
JOIN dim_time_period tp ON seed_obs.period_key = tp.period_key
WHERE m.derivation_type = 'base'
  AND sim.jaccard_similarity >= 0.3;
