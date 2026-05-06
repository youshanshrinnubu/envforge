"""Archive and restore snapshots as compressed bundles."""

import gzip
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from envforge.serializer import snapshot_to_dict, snapshot_from_dict
from envforge.snapshot import EnvSnapshot

DEFAULT_ARCHIVE_EXT = ".efz"


def archive_snapshot(snapshot: EnvSnapshot, dest_path: str, compress: bool = True) -> str:
    """Serialize and write a snapshot to a compressed archive file.

    Args:
        snapshot: The EnvSnapshot to archive.
        dest_path: Destination file path (will add .efz extension if missing).
        compress: Whether to gzip-compress the archive.

    Returns:
        The resolved path of the written archive file.
    """
    if not dest_path.endswith(DEFAULT_ARCHIVE_EXT):
        dest_path = dest_path + DEFAULT_ARCHIVE_EXT

    data = json.dumps(snapshot_to_dict(snapshot), indent=2).encode("utf-8")

    if compress:
        with gzip.open(dest_path, "wb") as fh:
            fh.write(data)
    else:
        with open(dest_path, "wb") as fh:
            fh.write(data)

    return os.path.abspath(dest_path)


def restore_snapshot(archive_path: str) -> EnvSnapshot:
    """Read and deserialize a snapshot from an archive file.

    Args:
        archive_path: Path to the .efz archive file.

    Returns:
        The restored EnvSnapshot.

    Raises:
        FileNotFoundError: If the archive does not exist.
        ValueError: If the file cannot be parsed.
    """
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    try:
        with gzip.open(archive_path, "rb") as fh:
            data = fh.read()
    except (OSError, gzip.BadGzipFile):
        with open(archive_path, "rb") as fh:
            data = fh.read()

    try:
        raw = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid archive format: {exc}") from exc

    return snapshot_from_dict(raw)


def archive_info(archive_path: str) -> dict:
    """Return metadata about an archive without fully restoring it."""
    snapshot = restore_snapshot(archive_path)
    size_bytes = os.path.getsize(archive_path)
    return {
        "path": os.path.abspath(archive_path),
        "size_bytes": size_bytes,
        "python_version": snapshot.python_version,
        "node_version": snapshot.node_version,
        "pip_package_count": len(snapshot.pip_packages),
        "env_var_count": len(snapshot.env_vars),
    }
