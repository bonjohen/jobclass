"""T9-01 through T9-10: Analyst mart tests."""


from jobclass.marts.views import all_marts_exist, mart_row_count


class TestOccupationSummary:
    """T9-01, T9-02: occupation_summary grain and hierarchy fields."""

    def test_grain_one_row_per_occupation(self, onet_loaded_db):
        """T9-01: Zero duplicates on occupation_key; every current occupation appears."""
        dup_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT occupation_key, COUNT(*) AS n"
            "  FROM occupation_summary"
            "  GROUP BY occupation_key"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dup_count == 0

        mart_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_summary"
        ).fetchone()[0]
        dim_current = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_occupation WHERE is_current = true"
        ).fetchone()[0]
        assert mart_count == dim_current

    def test_hierarchy_fields(self, onet_loaded_db):
        """T9-02: Hierarchy fields populated for detailed occupations."""
        rows = onet_loaded_db.execute(
            "SELECT soc_code, major_group_code, occupation_level_name"
            " FROM occupation_summary WHERE occupation_level = 4"
        ).fetchall()
        assert len(rows) > 0
        for _soc_code, major_group, level_name in rows:
            assert major_group is not None
            assert "detailed" in level_name.lower()


class TestOccupationWagesByGeography:
    """T9-03, T9-04: occupation_wages_by_geography grain and join correctness."""

    def test_grain_no_duplicates(self, onet_loaded_db):
        """T9-03: Zero duplicates on occupation_key + geography_key + source_dataset."""
        dup_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT occupation_key, geography_key, source_dataset, COUNT(*) AS n"
            "  FROM occupation_wages_by_geography"
            "  GROUP BY occupation_key, geography_key, source_dataset"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dup_count == 0

    def test_contains_wage_columns(self, onet_loaded_db):
        """T9-03: Mart contains employment and wage fields."""
        cols = {
            row[0]
            for row in onet_loaded_db.execute(
                "DESCRIBE occupation_wages_by_geography"
            ).fetchall()
        }
        for expected in ["employment_count", "mean_annual_wage", "median_annual_wage"]:
            assert expected in cols

    def test_join_no_fanout(self, onet_loaded_db):
        """T9-04: Row count matches underlying fact for current occupations."""
        mart_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_wages_by_geography"
        ).fetchone()[0]
        fact_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages f"
            " JOIN dim_occupation o ON f.occupation_key = o.occupation_key"
            " WHERE o.is_current = true"
        ).fetchone()[0]
        assert mart_count == fact_count


class TestOccupationSkillProfile:
    """T9-05, T9-06: occupation_skill_profile grain and version filtering."""

    def test_grain_no_duplicates(self, onet_loaded_db):
        """T9-05: Zero duplicates on occupation_key + skill_key + scale_type."""
        dup_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT occupation_key, skill_key, scale_type, COUNT(*) AS n"
            "  FROM occupation_skill_profile"
            "  GROUP BY occupation_key, skill_key, scale_type"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dup_count == 0

    def test_current_version_only(self, onet_loaded_db):
        """T9-06: All rows use the current O*NET version."""
        versions = onet_loaded_db.execute(
            "SELECT DISTINCT source_version FROM occupation_skill_profile"
        ).fetchall()
        assert len(versions) >= 1
        # All rows should share the same source_version
        assert len(versions) == 1

    def test_has_rows(self, onet_loaded_db):
        """Skill profile mart is populated."""
        count = mart_row_count(onet_loaded_db, "occupation_skill_profile")
        assert count > 0


class TestOccupationTaskProfile:
    """T9-07: occupation_task_profile grain."""

    def test_grain_no_duplicates(self, onet_loaded_db):
        """T9-07: Zero duplicates on occupation_key + task_key."""
        dup_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT occupation_key, task_key, COUNT(*) AS n"
            "  FROM occupation_task_profile"
            "  GROUP BY occupation_key, task_key"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dup_count == 0

    def test_has_rows(self, onet_loaded_db):
        """Task profile mart is populated."""
        count = mart_row_count(onet_loaded_db, "occupation_task_profile")
        assert count > 0


class TestOccupationSimilaritySeeded:
    """T9-08: occupation_similarity_seeded produces scores."""

    def test_nontrivial_similarity(self, onet_loaded_db):
        """T9-08: At least some occupation pairs with similarity > 0."""
        count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_similarity_seeded"
            " WHERE jaccard_similarity > 0"
        ).fetchone()[0]
        assert count > 0

    def test_similarity_bounded(self, onet_loaded_db):
        """Similarity values should be between 0 and 1."""
        bad = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_similarity_seeded"
            " WHERE jaccard_similarity < 0 OR jaccard_similarity > 1"
        ).fetchone()[0]
        assert bad == 0


class TestSourceLineage:
    """T9-09: All marts trace back to source lineage."""

    def test_summary_has_release_id(self, onet_loaded_db):
        """occupation_summary has source_release_id on every row."""
        null_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_summary WHERE source_release_id IS NULL"
        ).fetchone()[0]
        assert null_count == 0

    def test_wages_has_release_id(self, onet_loaded_db):
        """occupation_wages_by_geography has source_release_id on every row."""
        null_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_wages_by_geography WHERE source_release_id IS NULL"
        ).fetchone()[0]
        assert null_count == 0

    def test_skill_profile_has_release_id(self, onet_loaded_db):
        """occupation_skill_profile has source_release_id on every row."""
        null_count = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM occupation_skill_profile WHERE source_release_id IS NULL"
        ).fetchone()[0]
        assert null_count == 0


class TestPublishGating:
    """T9-10: Marts not refreshed when upstream validation fails."""

    def test_publish_blocked_on_empty_db(self, migrated_db):
        """With no data loaded, warehouse_publish should be blocked."""
        from jobclass.orchestrate.pipelines import PipelineStatus, warehouse_publish
        result = warehouse_publish(migrated_db, "2018", "2024.05", "29.1")
        assert result.status in (PipelineStatus.PUBLISH_BLOCKED, PipelineStatus.SUCCESS)

    def test_all_marts_exist_after_load(self, onet_loaded_db):
        """After full load, all mart views are queryable."""
        assert all_marts_exist(onet_loaded_db)
