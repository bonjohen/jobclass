-- ============================================================
-- Sample Analyst Queries for JobClass Warehouse
-- ============================================================

-- 1. How many people work as Software Developers nationally?
SELECT
    soc_code,
    occupation_title,
    employment_count,
    mean_annual_wage,
    median_annual_wage
FROM occupation_wages_by_geography
WHERE soc_code = '15-1252'
  AND geo_type = 'national';


-- 2. State-level wage distribution for Software Developers
SELECT
    geo_name,
    employment_count,
    mean_annual_wage,
    median_annual_wage,
    p10_hourly_wage,
    p90_hourly_wage
FROM occupation_wages_by_geography
WHERE soc_code = '15-1252'
  AND geo_type = 'state'
ORDER BY mean_annual_wage DESC;


-- 3. Core skills for Software Developers (importance scale)
SELECT
    skill_name,
    data_value AS importance_score,
    source_version
FROM occupation_skill_profile
WHERE soc_code = '15-1252'
  AND scale_type = 'IM'
ORDER BY data_value DESC;


-- 4. Core tasks for Software Developers
SELECT
    task_description,
    task_type,
    data_value AS relevance_score
FROM occupation_task_profile
WHERE soc_code = '15-1252'
ORDER BY data_value DESC;


-- 5. Occupations most similar to Software Developers (by shared skills)
SELECT
    soc_code_b AS similar_soc_code,
    title_b AS similar_occupation,
    shared_skills,
    jaccard_similarity
FROM occupation_similarity_seeded
WHERE soc_code_a = '15-1252'
ORDER BY jaccard_similarity DESC
LIMIT 10;


-- 6. Occupation hierarchy: all occupations under Computer and Mathematical major group
SELECT
    soc_code,
    occupation_title,
    occupation_level_name,
    is_leaf
FROM occupation_summary
WHERE major_group_code = '15-0000'
ORDER BY soc_code;


-- 7. Top 10 highest-paying occupations nationally
SELECT
    soc_code,
    occupation_title,
    mean_annual_wage,
    employment_count
FROM occupation_wages_by_geography
WHERE geo_type = 'national'
  AND mean_annual_wage IS NOT NULL
ORDER BY mean_annual_wage DESC
LIMIT 10;


-- 8. Employment projections for Software Developers
SELECT
    projection_cycle,
    employment_base,
    employment_projected,
    employment_change_pct,
    annual_openings,
    education_category
FROM fact_occupation_projections f
JOIN dim_occupation o ON f.occupation_key = o.occupation_key
WHERE o.soc_code = '15-1252';


-- 9. Run manifest: inspect the most recent pipeline run
SELECT
    run_id,
    pipeline_name,
    load_status,
    row_count_raw,
    row_count_stage,
    row_count_loaded,
    created_at,
    completed_at
FROM run_manifest
ORDER BY created_at DESC
LIMIT 5;


-- 10. Data lineage: trace a fact row back to source
SELECT
    f.fact_id,
    o.soc_code,
    o.occupation_title,
    g.geo_name,
    f.mean_annual_wage,
    f.source_dataset,
    f.source_release_id,
    f.load_timestamp
FROM fact_occupation_employment_wages f
JOIN dim_occupation o ON f.occupation_key = o.occupation_key
JOIN dim_geography g ON f.geography_key = g.geography_key
WHERE o.soc_code = '15-1252'
  AND g.geo_type = 'national';
