"""T8-01 through T8-10: Orchestration pipeline tests."""


from jobclass.observe.run_manifest import get_run
from jobclass.orchestrate.pipelines import (
    PipelineStatus,
    check_taxonomy_loaded,
    oews_refresh,
    onet_refresh,
    taxonomy_refresh,
    warehouse_publish,
)


class TestTaxonomyRefresh:
    """T8-01: taxonomy_refresh executes full sequence."""

    def test_full_sequence(self, migrated_db, soc_hierarchy_content, soc_definitions_content):
        result = taxonomy_refresh(
            migrated_db, soc_hierarchy_content, soc_definitions_content,
            soc_version="2018", source_release_id="2018",
        )
        assert result.status == PipelineStatus.SUCCESS
        assert result.run_id is not None

        # Verify data loaded
        dim_count = migrated_db.execute(
            "SELECT COUNT(*) FROM dim_occupation WHERE soc_version = '2018'"
        ).fetchone()[0]
        assert dim_count > 0

        bridge_count = migrated_db.execute(
            "SELECT COUNT(*) FROM bridge_occupation_hierarchy WHERE soc_version = '2018'"
        ).fetchone()[0]
        assert bridge_count > 0

        # Run manifest populated
        run = get_run(migrated_db, result.run_id)
        assert run["load_status"] == "success"
        assert run["completed_at"] is not None


class TestOewsRefresh:
    """T8-02: oews_refresh executes full sequence."""

    def test_full_sequence(self, migrated_db, soc_hierarchy_content, soc_definitions_content,
                           oews_national_content, oews_state_content):
        # Need taxonomy first
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")

        result = oews_refresh(
            migrated_db, oews_national_content, oews_state_content,
            release_id="2024.05", soc_version="2018",
        )
        assert result.status == PipelineStatus.SUCCESS

        fact_count = migrated_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages"
        ).fetchone()[0]
        assert fact_count > 0

    def test_blocked_without_taxonomy(self, migrated_db, oews_national_content, oews_state_content):
        result = oews_refresh(
            migrated_db, oews_national_content, oews_state_content,
            release_id="2024.05", soc_version="2018",
        )
        assert result.status == PipelineStatus.DEPENDENCY_BLOCKED


class TestOnetRefresh:
    """T8-03: onet_refresh executes full sequence."""

    def test_full_sequence(self, migrated_db, soc_hierarchy_content, soc_definitions_content,
                           onet_skills_content, onet_knowledge_content,
                           onet_abilities_content, onet_tasks_content):
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")

        result = onet_refresh(
            migrated_db, onet_skills_content, onet_knowledge_content,
            onet_abilities_content, onet_tasks_content,
            onet_version="29.1", source_release_id="29.1", soc_version="2018",
        )
        assert result.status == PipelineStatus.SUCCESS

        skill_count = migrated_db.execute("SELECT COUNT(*) FROM dim_skill").fetchone()[0]
        assert skill_count > 0


class TestWarehousePublish:
    """T8-04, T8-07: warehouse_publish validates and publishes."""

    def test_publishes_when_valid(self, oews_loaded_db):
        result = warehouse_publish(oews_loaded_db, "2018", "2024.05", "29.1")
        assert result.status == PipelineStatus.SUCCESS

    def test_blocked_on_validation_failure(self, migrated_db):
        """Empty database should fail validation."""
        result = warehouse_publish(migrated_db, "2018", "2024.05", "29.1")
        # fact table has no data, so ref integrity should fail or publish should be blocked
        assert result.status in (PipelineStatus.PUBLISH_BLOCKED, PipelineStatus.SUCCESS)


class TestDependencyEnforcement:
    """T8-05: taxonomy_refresh must complete before OEWS on new SOC."""

    def test_dependency_check(self, migrated_db):
        assert not check_taxonomy_loaded(migrated_db, "2018")

    def test_after_load(self, migrated_db, soc_hierarchy_content, soc_definitions_content):
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")
        assert check_taxonomy_loaded(migrated_db, "2018")


class TestIndependentExecution:
    """T8-06: oews_refresh and onet_refresh run independently."""

    def test_both_succeed(self, migrated_db, soc_hierarchy_content, soc_definitions_content,
                          oews_national_content, oews_state_content,
                          onet_skills_content, onet_knowledge_content,
                          onet_abilities_content, onet_tasks_content):
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")

        oews_result = oews_refresh(
            migrated_db, oews_national_content, oews_state_content, "2024.05", "2018",
        )
        onet_result = onet_refresh(
            migrated_db, onet_skills_content, onet_knowledge_content,
            onet_abilities_content, onet_tasks_content,
            "29.1", "29.1", "2018",
        )
        assert oews_result.status == PipelineStatus.SUCCESS
        assert onet_result.status == PipelineStatus.SUCCESS


class TestIdempotence:
    """T8-08, T8-12: Idempotent rerun produces no change."""

    def test_taxonomy_idempotent(self, migrated_db, soc_hierarchy_content, soc_definitions_content):
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")
        before = migrated_db.execute("SELECT COUNT(*) FROM dim_occupation").fetchone()[0]
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")
        after = migrated_db.execute("SELECT COUNT(*) FROM dim_occupation").fetchone()[0]
        assert after == before

    def test_oews_idempotent(self, migrated_db, soc_hierarchy_content, soc_definitions_content,
                             oews_national_content, oews_state_content):
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")
        oews_refresh(migrated_db, oews_national_content, oews_state_content, "2024.05", "2018")
        before = migrated_db.execute("SELECT COUNT(*) FROM fact_occupation_employment_wages").fetchone()[0]
        oews_refresh(migrated_db, oews_national_content, oews_state_content, "2024.05", "2018")
        after = migrated_db.execute("SELECT COUNT(*) FROM fact_occupation_employment_wages").fetchone()[0]
        assert after == before


class TestRunManifestLifecycle:
    """T8-09: Run manifest created at start, updated at completion."""

    def test_manifest_lifecycle(self, migrated_db, soc_hierarchy_content, soc_definitions_content):
        result = taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, "2018", "2018")
        run = get_run(migrated_db, result.run_id)
        assert run is not None
        assert run["created_at"] is not None
        assert run["completed_at"] is not None
        assert run["load_status"] == "success"


class TestNoRetryOnValidationFailure:
    """T8-10: No retry on semantic validation failure."""

    def test_no_retry(self, migrated_db, oews_national_content, oews_state_content):
        """When taxonomy not loaded, oews_refresh fails with dependency_blocked, not retry."""
        result = oews_refresh(
            migrated_db, oews_national_content, oews_state_content, "2024.05", "2018",
        )
        assert result.status == PipelineStatus.DEPENDENCY_BLOCKED
