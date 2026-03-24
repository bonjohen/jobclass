"""T10-01 through T10-08: Employment Projections pipeline tests."""


from jobclass.parse.projections import parse_employment_projections

# ============================================================
# T10-01: Parser tests
# ============================================================

class TestProjectionsParser:
    """T10-01: Parser extracts expected fields."""

    def test_extracts_known_occupations(self, projections_content):
        rows = parse_employment_projections(projections_content, "2024.1", "2022-2032")
        codes = {r.occupation_code for r in rows}
        assert "15-1252" in codes
        assert "15-1253" in codes
        assert "11-1021" in codes

    def test_employment_fields_numeric(self, projections_content):
        rows = parse_employment_projections(projections_content, "2024.1", "2022-2032")
        sw = [r for r in rows if r.occupation_code == "15-1252"][0]
        assert sw.employment_base == 1795300
        assert sw.employment_projected == 2094600
        assert sw.employment_change_abs == 299200
        assert abs(sw.employment_change_pct - 16.7) < 0.01
        assert sw.annual_openings == 140600

    def test_projection_cycle_set(self, projections_content):
        rows = parse_employment_projections(projections_content, "2024.1", "2022-2032")
        for r in rows:
            assert r.projection_cycle == "2022-2032"

    def test_metadata_present(self, projections_content):
        rows = parse_employment_projections(projections_content, "2024.1", "2022-2032")
        for r in rows:
            assert r.source_release_id == "2024.1"
            assert r.parser_version is not None

    def test_education_category(self, projections_content):
        rows = parse_employment_projections(projections_content, "2024.1", "2022-2032")
        sw = [r for r in rows if r.occupation_code == "15-1252"][0]
        assert sw.education_category == "Bachelor's degree"


# ============================================================
# T10-02: Staging contract
# ============================================================

class TestProjectionsStagingContract:
    """T10-02: staging table has required columns."""

    def test_required_columns(self, projections_loaded_db):
        cols = {
            row[0]
            for row in projections_loaded_db.execute(
                "DESCRIBE stage__bls__employment_projections"
            ).fetchall()
        }
        for expected in [
            "projection_cycle", "occupation_code", "base_year", "projection_year",
            "employment_base", "employment_projected", "source_release_id",
        ]:
            assert expected in cols


# ============================================================
# T10-03: Staging grain
# ============================================================

class TestProjectionsStagingGrain:
    """T10-03: No duplicate rows at declared grain."""

    def test_no_duplicates(self, projections_loaded_db):
        dup_count = projections_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT projection_cycle, occupation_code, source_release_id, COUNT(*) AS n"
            "  FROM stage__bls__employment_projections"
            "  GROUP BY projection_cycle, occupation_code, source_release_id"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dup_count == 0


# ============================================================
# T10-04: Fact grain
# ============================================================

class TestProjectionsFactGrain:
    """T10-04: No duplicate rows in fact table."""

    def test_no_duplicates(self, projections_loaded_db):
        dup_count = projections_loaded_db.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT projection_cycle, occupation_key, COUNT(*) AS n"
            "  FROM fact_occupation_projections"
            "  GROUP BY projection_cycle, occupation_key"
            "  HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        assert dup_count == 0


# ============================================================
# T10-05: Fact contract
# ============================================================

class TestProjectionsFactContract:
    """T10-05: Fact table has required fields."""

    def test_required_fields(self, projections_loaded_db):
        cols = {
            row[0]
            for row in projections_loaded_db.execute(
                "DESCRIBE fact_occupation_projections"
            ).fetchall()
        }
        for expected in [
            "projection_cycle", "occupation_key", "base_year", "projection_year",
            "employment_base", "employment_projected", "employment_change_pct",
            "source_release_id",
        ]:
            assert expected in cols


# ============================================================
# T10-06: Referential integrity
# ============================================================

class TestProjectionsRefIntegrity:
    """T10-06: Every occupation_key references valid dim_occupation."""

    def test_no_orphans(self, projections_loaded_db):
        orphans = projections_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_projections f"
            " LEFT JOIN dim_occupation o ON f.occupation_key = o.occupation_key"
            " WHERE o.occupation_key IS NULL"
        ).fetchone()[0]
        assert orphans == 0


# ============================================================
# T10-07: Idempotence
# ============================================================

class TestProjectionsIdempotence:
    """T10-07: Rerun produces no duplicates."""

    def test_rerun_no_duplicates(self, projections_loaded_db, projections_content):
        from jobclass.load.projections import load_fact_occupation_projections, load_projections_staging
        from jobclass.parse.projections import parse_employment_projections

        before = projections_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_projections"
        ).fetchone()[0]

        rows = parse_employment_projections(projections_content, "2024.1", "2022-2032")
        load_projections_staging(projections_loaded_db, rows, "2024.1")
        load_fact_occupation_projections(projections_loaded_db, "2024.1", "2018")

        after = projections_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_projections"
        ).fetchone()[0]
        assert after == before


# ============================================================
# T10-08: Pipeline integration
# ============================================================

class TestProjectionsRefreshPipeline:
    """T10-08: projections_refresh executes full sequence."""

    def test_full_sequence(self, oews_loaded_db, projections_content):
        from jobclass.observe.run_manifest import get_run
        from jobclass.orchestrate.pipelines import PipelineStatus, projections_refresh

        result = projections_refresh(
            oews_loaded_db, projections_content,
            source_release_id="2024.1",
            projection_cycle="2022-2032",
            soc_version="2018",
        )
        assert result.status == PipelineStatus.SUCCESS, f"Failed: {result.message}"
        assert result.run_id is not None

        fact_count = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_projections"
        ).fetchone()[0]
        assert fact_count > 0

        run = get_run(oews_loaded_db, result.run_id)
        assert run["load_status"] == "success"

    def test_blocked_without_taxonomy(self, migrated_db, projections_content):
        from jobclass.orchestrate.pipelines import PipelineStatus, projections_refresh

        result = projections_refresh(
            migrated_db, projections_content,
            source_release_id="2024.1",
            projection_cycle="2022-2032",
            soc_version="2018",
        )
        assert result.status == PipelineStatus.DEPENDENCY_BLOCKED
