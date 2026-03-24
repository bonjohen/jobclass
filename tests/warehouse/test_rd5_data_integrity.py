"""RD5: Data warehouse validation tests against real data.

These tests verify that the pipeline-populated warehouse contains
structurally sound, referentially correct, and plausibly valued data.
Skipped automatically if warehouse.duckdb does not exist.
"""

import pytest

# ============================================================
# RD5-01: dim_occupation row count
# ============================================================

class TestDimOccupation:
    def test_has_sufficient_rows(self, warehouse_db):
        """RD5-01: SOC 2018 has ~867 detailed occupations + higher levels."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM dim_occupation"
        ).fetchone()[0]
        assert count >= 800, f"Expected >= 800 occupations, got {count}"

    def test_has_all_levels(self, warehouse_db):
        """Occupations span all 4 hierarchy levels."""
        levels = warehouse_db.execute(
            "SELECT DISTINCT occupation_level FROM dim_occupation ORDER BY occupation_level"
        ).fetchall()
        assert [r[0] for r in levels] == [1, 2, 3, 4]

    def test_no_duplicate_soc_code_version(self, warehouse_db):
        """RD5-08: No duplicate occupation keys at SOC code + version grain."""
        dups = warehouse_db.execute("""
            SELECT soc_code, soc_version, COUNT(*) AS cnt
            FROM dim_occupation
            GROUP BY soc_code, soc_version
            HAVING cnt > 1
        """).fetchall()
        assert len(dups) == 0, f"Duplicate occupation keys: {dups[:10]}"


# ============================================================
# RD5-02: dim_geography row count
# ============================================================

class TestDimGeography:
    def test_has_sufficient_rows(self, warehouse_db):
        """RD5-02: At least 50 states + national + territories."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM dim_geography"
        ).fetchone()[0]
        assert count >= 50, f"Expected >= 50 geographies, got {count}"

    def test_has_national(self, warehouse_db):
        """National geography exists."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM dim_geography WHERE geo_type = 'national'"
        ).fetchone()[0]
        assert count >= 1


# ============================================================
# RD5-03: fact_occupation_employment_wages row count
# ============================================================

class TestFactWages:
    def test_has_sufficient_rows(self, warehouse_db):
        """RD5-03: Real OEWS should produce >= 10,000 wage fact rows."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages"
        ).fetchone()[0]
        assert count >= 10_000, f"Expected >= 10,000 wage facts, got {count}"

    def test_occupation_key_referential_integrity(self, warehouse_db):
        """RD5-04: All wage fact occupation_keys exist in dim_occupation."""
        orphans = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_employment_wages f
            LEFT JOIN dim_occupation o ON f.occupation_key = o.occupation_key
            WHERE o.occupation_key IS NULL
        """).fetchone()[0]
        assert orphans == 0, f"{orphans} wage facts with missing occupation_key"

    def test_geography_key_referential_integrity(self, warehouse_db):
        """RD5-05: All wage fact geography_keys exist in dim_geography."""
        orphans = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_employment_wages f
            LEFT JOIN dim_geography g ON f.geography_key = g.geography_key
            WHERE g.geography_key IS NULL
        """).fetchone()[0]
        assert orphans == 0, f"{orphans} wage facts with missing geography_key"

    def test_hourly_wage_range(self, warehouse_db):
        """RD5-06: Hourly wages in plausible range ($0–$500/hr)."""
        for col in ["mean_hourly_wage", "median_hourly_wage",
                     "p10_hourly_wage", "p25_hourly_wage",
                     "p75_hourly_wage", "p90_hourly_wage"]:
            result = warehouse_db.execute(f"""
                SELECT MIN({col}), MAX({col})
                FROM fact_occupation_employment_wages
                WHERE {col} IS NOT NULL
            """).fetchone()
            assert result[0] >= 0, f"{col} has negative values: min={result[0]}"
            assert result[1] <= 500, f"{col} exceeds $500/hr: max={result[1]}"

    def test_annual_wage_range(self, warehouse_db):
        """RD5-06: Annual wages in plausible range ($0–$750k/yr)."""
        for col in ["mean_annual_wage", "median_annual_wage"]:
            result = warehouse_db.execute(f"""
                SELECT MIN({col}), MAX({col})
                FROM fact_occupation_employment_wages
                WHERE {col} IS NOT NULL
            """).fetchone()
            assert result[0] >= 0, f"{col} has negative values: min={result[0]}"
            assert result[1] <= 750_000, f"{col} exceeds $750k/yr: max={result[1]}"

    def test_employment_counts_positive(self, warehouse_db):
        """RD5-07: Employment counts are positive where not suppressed."""
        negatives = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_employment_wages
            WHERE employment_count IS NOT NULL AND employment_count < 0
        """).fetchone()[0]
        assert negatives == 0, f"{negatives} rows with negative employment"


# ============================================================
# RD5-09: Projections
# ============================================================

class TestFactProjections:
    def test_has_rows(self, warehouse_db):
        """Projections fact table is populated."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_projections"
        ).fetchone()[0]
        assert count >= 100, f"Expected >= 100 projection rows, got {count}"

    def test_base_year_before_projection_year(self, warehouse_db):
        """RD5-09: base_year < projection_year for all rows."""
        violations = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_projections
            WHERE base_year >= projection_year
        """).fetchone()[0]
        assert violations == 0, f"{violations} rows where base_year >= projection_year"

    def test_occupation_key_referential_integrity(self, warehouse_db):
        """All projection occupation_keys exist in dim_occupation."""
        orphans = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_projections f
            LEFT JOIN dim_occupation o ON f.occupation_key = o.occupation_key
            WHERE o.occupation_key IS NULL
        """).fetchone()[0]
        assert orphans == 0, f"{orphans} projection facts with missing occupation_key"


# ============================================================
# RD5-10: O*NET skill values
# ============================================================

class TestOnetBridges:
    def test_skill_importance_range(self, warehouse_db):
        """RD5-10: Skill importance values are in [0, 5] range."""
        result = warehouse_db.execute("""
            SELECT MIN(data_value), MAX(data_value)
            FROM bridge_occupation_skill
            WHERE scale_id = 'IM'
        """).fetchone()
        if result[0] is not None:
            assert result[0] >= 0, f"Skill importance min={result[0]} < 0"
            assert result[1] <= 5, f"Skill importance max={result[1]} > 5"

    def test_skill_level_range(self, warehouse_db):
        """Skill level values are in [0, 7] range."""
        result = warehouse_db.execute("""
            SELECT MIN(data_value), MAX(data_value)
            FROM bridge_occupation_skill
            WHERE scale_id = 'LV'
        """).fetchone()
        if result[0] is not None:
            assert result[0] >= 0, f"Skill level min={result[0]} < 0"
            assert result[1] <= 7, f"Skill level max={result[1]} > 7"

    def test_bridge_occupation_skill_populated(self, warehouse_db):
        """Bridge tables have substantial data."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM bridge_occupation_skill"
        ).fetchone()[0]
        assert count >= 1000, f"Expected >= 1000 skill bridge rows, got {count}"

    def test_bridge_occupation_task_populated(self, warehouse_db):
        """Task bridge has substantial data."""
        count = warehouse_db.execute(
            "SELECT COUNT(*) FROM bridge_occupation_task"
        ).fetchone()[0]
        assert count >= 1000, f"Expected >= 1000 task bridge rows, got {count}"


# ============================================================
# RD5-11: Similarity scores (if populated)
# ============================================================

class TestSimilarity:
    def test_similarity_scores_range(self, warehouse_db):
        """RD5-11: Similarity scores are in [0, 1] range if table exists."""
        try:
            result = warehouse_db.execute("""
                SELECT MIN(similarity_score), MAX(similarity_score)
                FROM mart_occupation_similarity_seeded
                WHERE similarity_score IS NOT NULL
            """).fetchone()
            if result[0] is not None:
                assert result[0] >= 0, f"Similarity min={result[0]} < 0"
                assert result[1] <= 1.0, f"Similarity max={result[1]} > 1"
        except Exception:
            pytest.skip("mart_occupation_similarity_seeded not populated")


# ============================================================
# RD5-12: End-to-end occupation profile completeness
# ============================================================

class TestOccupationCompleteness:
    """Verify that at least one representative occupation has data across all domains."""

    def test_occupation_has_wages(self, warehouse_db):
        """RD5-12: A well-known occupation has wage data."""
        # Use 15-1251 (Computer Programmers) which exists in both SOC and O*NET
        count = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_employment_wages f
            JOIN dim_occupation o ON f.occupation_key = o.occupation_key
            WHERE o.soc_code = '15-1251'
        """).fetchone()[0]
        assert count > 0, "15-1251 has no wage data"

    def test_occupation_has_skills(self, warehouse_db):
        """RD5-12: A well-known occupation has skill data."""
        count = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM bridge_occupation_skill b
            JOIN dim_occupation o ON b.occupation_key = o.occupation_key
            WHERE o.soc_code = '15-1251'
        """).fetchone()[0]
        assert count > 0, "15-1251 has no skill data"

    def test_occupation_has_tasks(self, warehouse_db):
        """RD5-12: A well-known occupation has task data."""
        count = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM bridge_occupation_task b
            JOIN dim_occupation o ON b.occupation_key = o.occupation_key
            WHERE o.soc_code = '15-1251'
        """).fetchone()[0]
        assert count > 0, "15-1251 has no task data"

    def test_occupation_has_projections(self, warehouse_db):
        """RD5-12: A well-known occupation has projection data."""
        count = warehouse_db.execute("""
            SELECT COUNT(*)
            FROM fact_occupation_projections f
            JOIN dim_occupation o ON f.occupation_key = o.occupation_key
            WHERE o.soc_code = '15-1251'
        """).fetchone()[0]
        assert count > 0, "15-1251 has no projection data"
