"""Raw storage path builder utility."""

from pathlib import Path

from jobclass.config.settings import RAW_ROOT


def build_raw_path(
    source_name: str,
    dataset_name: str,
    source_release_id: str,
    run_id: str,
    filename: str,
    raw_root: Path | None = None,
) -> Path:
    """Build a raw storage path following the convention:
    raw/{source_name}/{dataset_name}/{source_release_id}/{run_id}/{filename}

    All components are required and must be non-empty strings.
    """
    root = raw_root or RAW_ROOT
    for name, value in [
        ("source_name", source_name),
        ("dataset_name", dataset_name),
        ("source_release_id", source_release_id),
        ("run_id", run_id),
        ("filename", filename),
    ]:
        if not value or not value.strip():
            raise ValueError(f"{name} must be a non-empty string, got: {value!r}")

    return root / source_name / dataset_name / source_release_id / run_id / filename


def ensure_raw_dir(path: Path) -> Path:
    """Ensure the parent directory of a raw storage path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
