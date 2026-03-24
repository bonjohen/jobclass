"""T11-01 through T11-09: End-to-end integration and portfolio deliverable tests."""

from jobclass.observe.run_manifest import get_run
from jobclass.orchestrate.pipelines import (
    PipelineStatus,
    oews_refresh,
    onet_refresh,
    projections_refresh,
    taxonomy_refresh,
    warehouse_publish,
)

# ============================================================
# T11-01: Full pipeline for Software Developers (15-1252)
# ============================================================


class TestFullPipeline:
    """T11-01: End-to-end pipeline for Software Developers."""

    def test_full_sequence(
        self,
        migrated_db,
        soc_hierarchy_content,
        soc_definitions_content,
        oews_national_content,
        oews_state_content,
        onet_skills_content,
        onet_knowledge_content,
        onet_abilities_content,
        onet_tasks_content,
        projections_content,
    ):
        soc_ver = "2018"
        oews_rel = "2024.05"
        onet_ver = "29.1"
        proj_rel = "2024.1"

        # taxonomy_refresh
        tax_result = taxonomy_refresh(
            migrated_db,
            soc_hierarchy_content,
            soc_definitions_content,
            soc_ver,
            soc_ver,
        )
        assert tax_result.status == PipelineStatus.SUCCESS

        # oews_refresh
        oews_result = oews_refresh(
            migrated_db,
            oews_national_content,
            oews_state_content,
            oews_rel,
            soc_ver,
        )
        assert oews_result.status == PipelineStatus.SUCCESS

        # onet_refresh
        onet_result = onet_refresh(
            migrated_db,
            onet_skills_content,
            onet_knowledge_content,
            onet_abilities_content,
            onet_tasks_content,
            onet_ver,
            onet_ver,
            soc_ver,
        )
        assert onet_result.status == PipelineStatus.SUCCESS

        # projections_refresh
        proj_result = projections_refresh(
            migrated_db,
            projections_content,
            proj_rel,
            "2022-2032",
            soc_ver,
        )
        assert proj_result.status == PipelineStatus.SUCCESS

        # warehouse_publish
        pub_result = warehouse_publish(migrated_db, soc_ver, oews_rel, onet_ver)
        assert pub_result.status == PipelineStatus.SUCCESS

        # All run manifests show success
        for run_id in [tax_result.run_id, oews_result.run_id, onet_result.run_id, proj_result.run_id]:
            run = get_run(migrated_db, run_id)
            assert run["load_status"] == "success"

        # All mart views queryable
        for view in [
            "occupation_summary",
            "occupation_wages_by_geography",
            "occupation_skill_profile",
            "occupation_task_profile",
        ]:
            count = migrated_db.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
            assert count > 0


# ============================================================
# T11-02 through T11-04: Verification checks
# ============================================================


class TestOccupationMapping:
    """T11-02: Occupation code maps to active SOC version."""

    def test_software_developers_mapped(self, onet_loaded_db):
        row = onet_loaded_db.execute(
            "SELECT occupation_key, soc_version, is_current FROM dim_occupation"
            " WHERE soc_code = '15-1252' AND soc_version = '2018'"
        ).fetchone()
        assert row is not None
        assert row[2] is True  # is_current


class TestOewsFactGrain:
    """T11-03: OEWS fact row is unique at declared grain."""

    def test_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT reference_period, geography_key, industry_key,"
            "         ownership_code, occupation_key, source_dataset,"
            "         COUNT(*) AS n"
            "  FROM fact_occupation_employment_wages"
            "  GROUP BY reference_period, geography_key, industry_key,"
            "           ownership_code, occupation_key, source_dataset"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dups == 0


class TestOnetBridgeIntegrity:
    """T11-04: O*NET bridge rows reference valid descriptor dimensions."""

    def test_skill_bridge_refs(self, onet_loaded_db):
        orphans = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM bridge_occupation_skill b"
            " LEFT JOIN dim_skill s ON b.skill_key = s.skill_key"
            " WHERE s.skill_key IS NULL"
        ).fetchone()[0]
        assert orphans == 0

    def test_task_bridge_refs(self, onet_loaded_db):
        orphans = onet_loaded_db.execute(
            "SELECT COUNT(*) FROM bridge_occupation_task b"
            " LEFT JOIN dim_task t ON b.task_key = t.task_key"
            " WHERE t.task_key IS NULL"
        ).fetchone()[0]
        assert orphans == 0


# ============================================================
# T11-05, T11-06: Analyst queries
# ============================================================


class TestAnalystQueries:
    """T11-05, T11-06: Analyst queries for Software Developers."""

    def test_wage_distribution_by_geography(self, onet_loaded_db):
        """T11-05: State-level wage distribution for Software Developers."""
        rows = onet_loaded_db.execute(
            "SELECT geo_name, mean_annual_wage FROM occupation_wages_by_geography WHERE soc_code = '15-1252'"
        ).fetchall()
        # Should have at least some rows (national + states in test data)
        assert len(rows) >= 1

    def test_core_skills(self, onet_loaded_db):
        """T11-06: Core skills for Software Developers."""
        rows = onet_loaded_db.execute(
            "SELECT skill_name, data_value FROM occupation_skill_profile WHERE soc_code = '15-1252'"
        ).fetchall()
        assert len(rows) >= 1
        for name, _value in rows:
            assert name is not None

    def test_core_tasks(self, onet_loaded_db):
        """T11-07: Core tasks for Software Developers."""
        rows = onet_loaded_db.execute(
            "SELECT task_description FROM occupation_task_profile WHERE soc_code = '15-1252'"
        ).fetchall()
        assert len(rows) >= 1
        for (desc,) in rows:
            assert desc is not None


# ============================================================
# T11-08: Idempotent rerun
# ============================================================


class TestFullIdempotence:
    """T11-08: Full pipeline re-execution produces no duplicates."""

    def test_full_rerun_no_duplicates(
        self,
        migrated_db,
        soc_hierarchy_content,
        soc_definitions_content,
        oews_national_content,
        oews_state_content,
        onet_skills_content,
        onet_knowledge_content,
        onet_abilities_content,
        onet_tasks_content,
    ):
        soc_ver = "2018"
        oews_rel = "2024.05"
        onet_ver = "29.1"

        # First run
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, soc_ver, soc_ver)
        oews_refresh(migrated_db, oews_national_content, oews_state_content, oews_rel, soc_ver)
        onet_refresh(
            migrated_db,
            onet_skills_content,
            onet_knowledge_content,
            onet_abilities_content,
            onet_tasks_content,
            onet_ver,
            onet_ver,
            soc_ver,
        )

        tables = [
            "dim_occupation",
            "fact_occupation_employment_wages",
            "dim_skill",
            "bridge_occupation_skill",
            "bridge_occupation_task",
        ]
        before = {t: migrated_db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}

        # Second run (rerun)
        taxonomy_refresh(migrated_db, soc_hierarchy_content, soc_definitions_content, soc_ver, soc_ver)
        oews_refresh(migrated_db, oews_national_content, oews_state_content, oews_rel, soc_ver)
        onet_refresh(
            migrated_db,
            onet_skills_content,
            onet_knowledge_content,
            onet_abilities_content,
            onet_tasks_content,
            onet_ver,
            onet_ver,
            soc_ver,
        )

        after = {t: migrated_db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
        assert after == before


# ============================================================
# T11-09: Deliverables present
# ============================================================


class TestDeliverablesPresent:
    """T11-09: All deliverables DL-1 through DL-8 exist."""

    def test_deliverables(self):
        """Check that key files exist."""
        from pathlib import Path

        root = Path(__file__).parent.parent.parent

        # DL-1: Phased release plan
        assert (root / "docs" / "specs" / "archive" / "phased_release_plan.md").exists()
        # DL-2: Source manifest
        assert (root / "config" / "source_manifest.yaml").exists()
        # DL-3: Test plan
        assert (root / "docs" / "specs" / "archive" / "test_plan.md").exists()
        # DL-4/DL-5: Run manifest and validation report (code exists)
        assert (root / "src" / "jobclass" / "observe" / "run_manifest.py").exists()
        assert (root / "src" / "jobclass" / "observe" / "reporters.py").exists()
        # DL-6: Schema documentation
        assert (root / "docs" / "schema.md").exists()
        # DL-7: Sample queries
        assert (root / "docs" / "sample_queries.sql").exists()
        # DL-8: Design document
        assert (root / "docs" / "specs" / "archive" / "base_design_document.md").exists()
