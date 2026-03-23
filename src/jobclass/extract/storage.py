"""Raw storage writer — immutable artifact storage with path convention enforcement."""

from pathlib import Path

from jobclass.utils.paths import build_raw_path, ensure_raw_dir


class StorageConflictError(Exception):
    """Raised when attempting to overwrite an existing raw artifact."""


def store_raw_artifact(
    content: bytes,
    source_name: str,
    dataset_name: str,
    source_release_id: str,
    run_id: str,
    filename: str,
    raw_root: Path | None = None,
) -> Path:
    """Store a raw artifact immutably at the canonical path.

    Raises StorageConflictError if the file already exists (NFR-2: never overwrite).
    Returns the path where the file was written.
    """
    path = build_raw_path(source_name, dataset_name, source_release_id, run_id, filename, raw_root=raw_root)

    if path.exists():
        raise StorageConflictError(f"Raw artifact already exists at {path}")

    ensure_raw_dir(path)
    path.write_bytes(content)
    return path
