"""T2-14, T2-15: Run manifest creation and uniqueness tests."""

from jobclass.config.database import apply_migrations
from jobclass.observe.run_manifest import create_run_record, generate_run_id, get_run


class TestRunManifestCreation:
    """T2-14: Run manifest creation inserts record with all required fields."""

    def test_creates_record_with_all_fields(self, db, tmp_path):
        # Apply migration to create table
        mdir = tmp_path / "migrations"
        mdir.mkdir()
        import shutil
        from pathlib import Path

        src_mdir = Path(__file__).parent.parent.parent / "migrations"
        for f in src_mdir.glob("*.sql"):
            shutil.copy(f, mdir / f.name)
        apply_migrations(db, migrations_dir=mdir)

        run_id = generate_run_id()
        create_run_record(
            db,
            run_id=run_id,
            pipeline_name="soc_refresh",
            dataset_name="soc_hierarchy",
            source_name="soc",
            source_url="https://example.com/soc.csv",
            source_release_id="2018",
            downloaded_at="2026-03-23T09:15:00Z",
            parser_name="soc_hierarchy_parser",
            parser_version="1.0.0",
            raw_checksum="abc123def456",
        )

        record = get_run(db, run_id)
        assert record is not None
        assert record["run_id"] == run_id
        assert record["pipeline_name"] == "soc_refresh"
        assert record["dataset_name"] == "soc_hierarchy"
        assert record["source_name"] == "soc"
        assert record["source_url"] == "https://example.com/soc.csv"
        assert record["source_release_id"] == "2018"
        assert record["downloaded_at"] is not None
        assert record["parser_name"] == "soc_hierarchy_parser"
        assert record["parser_version"] == "1.0.0"
        assert record["raw_checksum"] == "abc123def456"


class TestRunIdUniqueness:
    """T2-15: Run manifest run_id is unique across creations."""

    def test_100_unique_run_ids(self):
        ids = {generate_run_id() for _ in range(100)}
        assert len(ids) == 100
