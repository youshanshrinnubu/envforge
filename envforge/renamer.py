"""Rename snapshots: update the snapshot name/label and persist the change."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from envforge.serializer import load_snapshot, save_snapshot
from envforge.snapshot import EnvSnapshot


@dataclass
class RenameResult:
    old_name: str
    new_name: str
    path: str
    success: bool
    error: Optional[str] = field(default=None)

    def __bool__(self) -> bool:  # noqa: D105
        return self.success


def rename_snapshot_file(src: str, dst: str, *, overwrite: bool = False) -> RenameResult:
    """Rename a snapshot JSON file on disk.

    Parameters
    ----------
    src:
        Absolute or relative path to the existing snapshot file.
    dst:
        Destination path (or directory; if a directory the filename is kept).
    overwrite:
        When *False* (default) raise an error if *dst* already exists.
    """
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    if not dst.endswith(".json"):
        dst += ".json"

    old_name = os.path.splitext(os.path.basename(src))[0]
    new_name = os.path.splitext(os.path.basename(dst))[0]

    if not os.path.isfile(src):
        return RenameResult(old_name, new_name, src, False, f"Source file not found: {src}")

    if os.path.exists(dst) and not overwrite:
        return RenameResult(old_name, new_name, dst, False, f"Destination already exists: {dst}")

    try:
        snapshot: EnvSnapshot = load_snapshot(src)
        # Embed the new logical name inside the snapshot metadata if present.
        if hasattr(snapshot, "metadata") and isinstance(snapshot.metadata, dict):
            snapshot.metadata["name"] = new_name
        save_snapshot(snapshot, dst)
        os.remove(src)
    except Exception as exc:  # pragma: no cover
        return RenameResult(old_name, new_name, dst, False, str(exc))

    return RenameResult(old_name, new_name, dst, True)


def update_snapshot_label(snapshot: EnvSnapshot, label: str) -> EnvSnapshot:
    """Return a copy of *snapshot* with its metadata 'name' field set to *label*."""
    if not hasattr(snapshot, "metadata") or snapshot.metadata is None:
        snapshot.metadata = {}
    snapshot.metadata["name"] = label
    return snapshot
