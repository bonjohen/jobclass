-- Migration 005: Analyst mart views (Phase 9)

-- ============================================================
-- occupation_summary: one row per current occupation with hierarchy fields
-- ============================================================
CREATE OR REPLACE VIEW occupation_summary AS
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    o.occupation_level,
    o.occupation_level_name,
    o.parent_soc_code,
    o.major_group_code,
    o.minor_group_code,
    o.broad_occupation_code,
    o.detailed_occupation_code,
    o.occupation_definition,
    o.soc_version,
    o.is_leaf,
    o.is_current,
    o.source_release_id
FROM dim_occupation o
WHERE o.is_current = true;


-- ============================================================
-- occupation_wages_by_geography: employment and wage measures by occupation × geography
-- ============================================================
CREATE OR REPLACE VIEW occupation_wages_by_geography AS
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    g.geography_key,
    g.geo_type,
    g.geo_code,
    g.geo_name,
    f.employment_count,
    f.mean_hourly_wage,
    f.mean_annual_wage,
    f.median_hourly_wage,
    f.median_annual_wage,
    f.p10_hourly_wage,
    f.p25_hourly_wage,
    f.p75_hourly_wage,
    f.p90_hourly_wage,
    f.source_dataset,
    f.source_release_id
FROM fact_occupation_employment_wages f
JOIN dim_occupation o ON f.occupation_key = o.occupation_key
JOIN dim_geography g ON f.geography_key = g.geography_key
WHERE o.is_current = true;


-- ============================================================
-- occupation_skill_profile: occupation-to-skill relationships (current O*NET version)
-- ============================================================
CREATE OR REPLACE VIEW occupation_skill_profile AS
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    s.skill_key,
    s.element_id    AS skill_id,
    s.element_name  AS skill_name,
    b.scale_id      AS scale_type,
    b.data_value,
    b.n,
    b.source_version,
    b.source_release_id
FROM bridge_occupation_skill b
JOIN dim_occupation o ON b.occupation_key = o.occupation_key
JOIN dim_skill s ON b.skill_key = s.skill_key
WHERE o.is_current = true
  AND s.is_current = true;


-- ============================================================
-- occupation_task_profile: occupation-to-task relationships
-- ============================================================
CREATE OR REPLACE VIEW occupation_task_profile AS
SELECT
    o.occupation_key,
    o.soc_code,
    o.occupation_title,
    t.task_key,
    t.task_id,
    t.task          AS task_description,
    t.task_type,
    b.data_value,
    b.n,
    b.source_version,
    b.source_release_id
FROM bridge_occupation_task b
JOIN dim_occupation o ON b.occupation_key = o.occupation_key
JOIN dim_task t ON b.task_key = t.task_key
WHERE o.is_current = true
  AND t.is_current = true;


-- ============================================================
-- occupation_similarity_seeded: cosine similarity on skill importance scores
-- O*NET rates ALL 35 skills for ALL occupations (binary presence = always 100%).
-- Cosine similarity on the importance (IM) score vectors captures which
-- occupations emphasise the same skills, not just which skills exist.
-- ============================================================
CREATE OR REPLACE VIEW occupation_similarity_seeded AS
WITH occ_skill_scores AS (
    SELECT
        b.occupation_key,
        s.element_id,
        AVG(b.data_value) AS importance
    FROM bridge_occupation_skill b
    JOIN dim_skill s ON b.skill_key = s.skill_key
    JOIN dim_occupation o ON b.occupation_key = o.occupation_key
    WHERE o.is_current = true
      AND s.is_current = true
      AND b.scale_id = 'IM'
    GROUP BY b.occupation_key, s.element_id
),
norms AS (
    SELECT occupation_key,
           SQRT(SUM(importance * importance)) AS norm,
           COUNT(*) AS total_skills
    FROM occ_skill_scores
    GROUP BY occupation_key
),
dot_products AS (
    SELECT
        a.occupation_key AS occupation_key_a,
        b.occupation_key AS occupation_key_b,
        SUM(a.importance * b.importance) AS dot_product,
        COUNT(*) AS shared_skills
    FROM occ_skill_scores a
    JOIN occ_skill_scores b ON a.element_id = b.element_id
                           AND a.occupation_key < b.occupation_key
    GROUP BY a.occupation_key, b.occupation_key
)
SELECT
    d.occupation_key_a,
    oa.soc_code  AS soc_code_a,
    oa.occupation_title AS title_a,
    d.occupation_key_b,
    ob.soc_code  AS soc_code_b,
    ob.occupation_title AS title_b,
    d.shared_skills,
    na.total_skills AS total_skills_a,
    nb.total_skills AS total_skills_b,
    ROUND(d.dot_product / (na.norm * nb.norm), 4) AS jaccard_similarity
FROM dot_products d
JOIN dim_occupation oa ON d.occupation_key_a = oa.occupation_key
JOIN dim_occupation ob ON d.occupation_key_b = ob.occupation_key
JOIN norms na ON d.occupation_key_a = na.occupation_key
JOIN norms nb ON d.occupation_key_b = nb.occupation_key;
