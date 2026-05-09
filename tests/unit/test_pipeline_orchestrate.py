"""Unit tests for orchestrate/pipelines.py core logic paths (F-11)."""

from __future__ import annotations

import duckdb
import pytest

from jobclass.orchestrate.pipelines import (
    PipelineResult,
    PipelineStatus,
    check_taxonomy_loaded,
)


class TestPipelineStatus:
    """PipelineStatus enum values and string behavior."""

    def test_status_values(self):
        assert PipelineStatus.SUCCESS == "success"
        assert PipelineStatus.VALIDATION_FAILURE == "validation_failure"
        assert PipelineStatus.LOAD_FAILURE == "load_failure"
        assert PipelineStatus.DEPENDENCY_BLOCKED == "dependency_blocked"
        assert PipelineStatus.PUBLISH_BLOCKED == "publish_blocked"

    def test_status_is_string(self):
        assert isinstance(PipelineStatus.SUCCESS, str)
        assert str(PipelineStatus.LOAD_FAILURE) == "load_failure"

    def test_all_statuses_count(self):
        assert len(PipelineStatus) == 5


class TestPipelineResult:
    """PipelineResult dataclass construction and defaults."""

    def test_minimal_result(self):
        r = PipelineResult(pipeline_name="test", status=PipelineStatus.SUCCESS)
        assert r.pipeline_name == "test"
        assert r.status == PipelineStatus.SUCCESS
        assert r.run_id is None
        assert r.message == ""
        assert r.validation_results == []

    def test_full_result(self):
        r = PipelineResult(
            pipeline_name="oews_refresh",
            status=PipelineStatus.VALIDATION_FAILURE,
            run_id="run-123",
            message="2 checks failed",
            validation_results=["fake_result"],
        )
        assert r.run_id == "run-123"
        assert r.message == "2 checks failed"
        assert len(r.validation_results) == 1

    def test_failure_result_has_message(self):
        r = PipelineResult(
            pipeline_name="taxonomy_refresh",
            status=PipelineStatus.LOAD_FAILURE,
            message="table not found",
        )
        assert r.status == PipelineStatus.LOAD_FAILURE
        assert "table not found" in r.message


class TestCheckTaxonomyLoaded:
    """check_taxonomy_loaded against in-memory DuckDB."""

    @pytest.fixture()
    def conn(self):
        c = duckdb.connect(":memory:")
        c.execute("CREATE TABLE dim_occupation (soc_code VARCHAR, soc_version VARCHAR, occupation_title VARCHAR)")
        yield c
        c.close()

    def test_empty_table_returns_false(self, conn):
        assert check_taxonomy_loaded(conn, "2018") is False

    def test_loaded_version_returns_true(self, conn):
        conn.execute("INSERT INTO dim_occupation VALUES ('11-1011', '2018', 'Chief Executives')")
        assert check_taxonomy_loaded(conn, "2018") is True

    def test_different_version_returns_false(self, conn):
        conn.execute("INSERT INTO dim_occupation VALUES ('11-1011', '2018', 'Chief Executives')")
        assert check_taxonomy_loaded(conn, "2010") is False

    def test_missing_table_returns_false(self):
        c = duckdb.connect(":memory:")
        assert check_taxonomy_loaded(c, "2018") is False
        c.close()
