"""T1-02, T1-03: Path-builder utility tests."""

import pytest

from jobclass.utils.paths import build_raw_path


def test_build_raw_path_correct_structure(tmp_path):
    """T1-02: Output matches raw/{source}/{dataset}/{release_id}/{run_id}/{filename}."""
    result = build_raw_path(
        source_name="bls",
        dataset_name="oews_state",
        source_release_id="2024.05",
        run_id="2026-03-23T09-15-00Z",
        filename="state_M2024_dl.xlsx",
        raw_root=tmp_path / "raw",
    )
    expected = tmp_path / "raw" / "bls" / "oews_state" / "2024.05" / "2026-03-23T09-15-00Z" / "state_M2024_dl.xlsx"
    assert result == expected


def test_build_raw_path_various_sources(tmp_path):
    """T1-02: Works for all source types."""
    root = tmp_path / "raw"
    for source, dataset in [("soc", "hierarchy"), ("onet", "skills"), ("bls", "projections")]:
        result = build_raw_path(source, dataset, "v1", "run1", "file.csv", raw_root=root)
        assert result.parts[-5] == source
        assert result.parts[-4] == dataset


@pytest.mark.parametrize(
    "kwargs",
    [
        {"source_name": "", "dataset_name": "d", "source_release_id": "r", "run_id": "x", "filename": "f"},
        {"source_name": "s", "dataset_name": "", "source_release_id": "r", "run_id": "x", "filename": "f"},
        {"source_name": "s", "dataset_name": "d", "source_release_id": "", "run_id": "x", "filename": "f"},
        {"source_name": "s", "dataset_name": "d", "source_release_id": "r", "run_id": "", "filename": "f"},
        {"source_name": "s", "dataset_name": "d", "source_release_id": "r", "run_id": "x", "filename": ""},
        {"source_name": "  ", "dataset_name": "d", "source_release_id": "r", "run_id": "x", "filename": "f"},
    ],
)
def test_build_raw_path_rejects_empty_components(kwargs, tmp_path):
    """T1-03: Raises ValueError for empty or whitespace components."""
    with pytest.raises(ValueError):
        build_raw_path(**kwargs, raw_root=tmp_path)


def test_build_raw_path_rejects_none():
    """T1-03: Raises ValueError/TypeError for None components."""
    with pytest.raises((ValueError, TypeError)):
        build_raw_path(None, "d", "r", "x", "f")
