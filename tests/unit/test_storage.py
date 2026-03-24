"""T2-05, T2-06: Raw storage writer tests."""

import pytest

from jobclass.extract.download import compute_checksum
from jobclass.extract.storage import StorageConflictError, store_raw_artifact


class TestStoreRawArtifact:
    """T2-05: Storage writer creates file at correct path with identical content."""

    def test_stores_at_correct_path(self, tmp_path):
        content = b"test csv data"
        raw_root = tmp_path / "raw"
        raw_root.mkdir()

        path = store_raw_artifact(
            content=content,
            source_name="bls",
            dataset_name="oews_state",
            source_release_id="2024.05",
            run_id="run-001",
            filename="state.xlsx",
            raw_root=raw_root,
        )

        assert path.exists()
        assert path.read_bytes() == content
        assert "bls" in str(path)
        assert "oews_state" in str(path)
        assert "2024.05" in str(path)
        assert "run-001" in str(path)
        assert path.name == "state.xlsx"

    def test_checksum_matches_after_storage(self, tmp_path):
        content = b"important data"
        raw_root = tmp_path / "raw"
        raw_root.mkdir()

        path = store_raw_artifact(
            content=content,
            source_name="soc",
            dataset_name="hierarchy",
            source_release_id="2018",
            run_id="run-002",
            filename="soc.csv",
            raw_root=raw_root,
        )

        assert compute_checksum(path.read_bytes()) == compute_checksum(content)


class TestStorageImmutability:
    """T2-06: Storage writer does not overwrite existing files."""

    def test_raises_on_duplicate_write(self, tmp_path):
        content = b"original data"
        raw_root = tmp_path / "raw"
        raw_root.mkdir()
        kwargs = dict(
            source_name="bls",
            dataset_name="oews_national",
            source_release_id="2024.05",
            run_id="run-001",
            filename="nat.xlsx",
            raw_root=raw_root,
        )

        store_raw_artifact(content=content, **kwargs)

        with pytest.raises(StorageConflictError):
            store_raw_artifact(content=b"different data", **kwargs)

        # Original content preserved
        from jobclass.utils.paths import build_raw_path

        path = build_raw_path(**{k: v for k, v in kwargs.items()})
        assert path.read_bytes() == content
