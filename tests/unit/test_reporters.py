"""T7-01 through T7-07: Observability and run reporting tests."""


from jobclass.observe.reporters import (
    inspect_run,
    report_reconciliation,
    report_row_count_delta,
    report_schema_drift_from_snapshots,
    report_top_measure_deltas,
)
from jobclass.observe.run_manifest import (
    create_run_record,
    generate_run_id,
    get_run,
    update_run_counts,
)


class TestRunManifestCompletion:
    """T7-01: Run manifest completion update populates all required fields."""

    def test_completion_fields_populated(self, migrated_db):
        run_id = generate_run_id()
        create_run_record(
            migrated_db, run_id=run_id, pipeline_name="oews_refresh",
            dataset_name="oews_national", source_name="bls",
        )
        update_run_counts(
            migrated_db, run_id,
            row_count_raw=1500, row_count_stage=1400, row_count_loaded=1300,
            load_status="success", validation_summary="3 checks passed",
        )
        run = get_run(migrated_db, run_id)
        assert run["row_count_raw"] == 1500
        assert run["row_count_stage"] == 1400
        assert run["row_count_loaded"] == 1300
        assert run["load_status"] == "success"
        assert run["validation_summary"] == "3 checks passed"
        assert run["completed_at"] is not None


class TestRowCountDeltaReporter:
    """T7-02, T7-03: Row-count delta reporter."""

    def test_computes_delta_vs_prior(self, migrated_db):
        """T7-02: Correct delta against prior successful run."""
        # Prior run
        prior_id = generate_run_id()
        create_run_record(
            migrated_db, run_id=prior_id, pipeline_name="oews_refresh",
            dataset_name="oews_national", source_name="bls",
        )
        update_run_counts(migrated_db, prior_id, row_count_loaded=1000, load_status="success")

        # Current run
        current_id = generate_run_id()
        create_run_record(
            migrated_db, run_id=current_id, pipeline_name="oews_refresh",
            dataset_name="oews_national", source_name="bls",
        )
        update_run_counts(migrated_db, current_id, row_count_loaded=1050, load_status="success")

        report = report_row_count_delta(migrated_db, "oews_national", current_id)
        assert report.current_count == 1050
        assert report.prior_count == 1000
        assert report.absolute_change == 50
        assert abs(report.pct_change - 5.0) < 0.1

    def test_handles_first_run(self, migrated_db):
        """T7-03: First run returns no-prior indicator."""
        run_id = generate_run_id()
        create_run_record(
            migrated_db, run_id=run_id, pipeline_name="new_pipeline",
            dataset_name="new_dataset", source_name="new_source",
        )
        update_run_counts(migrated_db, run_id, row_count_loaded=500, load_status="success")

        report = report_row_count_delta(migrated_db, "new_dataset", run_id)
        assert report.prior_run_id is None
        assert report.prior_count is None


class TestSchemaDriftReporter:
    """T7-04: Schema drift report emitter."""

    def test_produces_structured_output(self):
        prior_schema = {"col_a": "INTEGER", "col_b": "TEXT", "col_c": "DOUBLE"}
        current_schema = {"col_a": "INTEGER", "col_b": "TEXT", "col_d": "BOOLEAN"}
        report = report_schema_drift_from_snapshots(
            "oews_national", "2023.05", "2024.05", prior_schema, current_schema,
        )
        assert report.dataset_name == "oews_national"
        assert report.has_drift
        change_cols = {c.column_name for c in report.changes}
        assert "col_c" in change_cols  # removed
        assert "col_d" in change_cols  # added


class TestMeasureDeltaReporter:
    """T7-05: Top measure delta reporter."""

    def test_ranks_by_change(self):
        prior = {f"occ_{i}": float(50000 + i * 1000) for i in range(10)}
        current = dict(prior)
        current["occ_3"] = prior["occ_3"] * 1.5  # 50% increase
        current["occ_7"] = prior["occ_7"] * 0.7  # 30% decrease

        report = report_top_measure_deltas("oews_national", "mean_annual_wage", prior, current, top_n=5)
        assert len(report.deltas) <= 5
        assert report.deltas[0].group_key == "occ_3"  # biggest change


class TestReconciliationReporter:
    """T7-06: Reconciliation summary reporter."""

    def test_reports_match(self):
        report = report_reconciliation(
            "oews_national", "total_employment", 155_000_000, 155_500_000,
        )
        assert report.matches  # within 1% tolerance
        assert abs(report.pct_difference) < 1.0

    def test_reports_mismatch(self):
        report = report_reconciliation(
            "oews_national", "total_employment", 155_000_000, 170_000_000,
        )
        assert not report.matches  # >1% tolerance


class TestRunInspection:
    """T7-07: Run inspection view returns complete metadata."""

    def test_single_query_complete_picture(self, migrated_db):
        run_id = generate_run_id()
        create_run_record(
            migrated_db, run_id=run_id, pipeline_name="oews_refresh",
            dataset_name="oews_national", source_name="bls",
            source_release_id="2024.05",
        )
        update_run_counts(
            migrated_db, run_id,
            row_count_raw=2000, row_count_stage=1800, row_count_loaded=1700,
            load_status="success", validation_summary="all passed",
        )

        inspection = inspect_run(migrated_db, run_id)
        assert inspection is not None
        assert inspection.run_id == run_id
        assert inspection.pipeline_name == "oews_refresh"
        assert inspection.dataset_name == "oews_national"
        assert inspection.source_release_id == "2024.05"
        assert inspection.row_count_raw == 2000
        assert inspection.row_count_stage == 1800
        assert inspection.row_count_loaded == 1700
        assert inspection.load_status == "success"
        assert inspection.validation_summary == "all passed"
        assert inspection.created_at is not None
        assert inspection.completed_at is not None

    def test_missing_run_returns_none(self, migrated_db):
        result = inspect_run(migrated_db, "nonexistent-run-id")
        assert result is None
