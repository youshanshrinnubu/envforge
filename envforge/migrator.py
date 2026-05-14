"""Snapshot migration: upgrade snapshots from older schema versions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from envforge.snapshot import EnvSnapshot

CURRENT_SCHEMA_VERSION = 2


@dataclass
class MigrationResult:
    snapshot: EnvSnapshot
    original_version: int
    target_version: int
    steps_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return self.original_version != self.target_version


def _migrate_v0_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """v0 -> v1: wrap bare pip list strings into {name, version} dicts."""
    packages = data.get("pip_packages", [])
    upgraded: List[Dict[str, str]] = []
    for pkg in packages:
        if isinstance(pkg, str):
            parts = pkg.split("==", 1)
            upgraded.append({"name": parts[0], "version": parts[1] if len(parts) == 2 else ""})
        else:
            upgraded.append(pkg)
    data["pip_packages"] = upgraded
    return data


def _migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """v1 -> v2: rename 'node' key to 'node_version'."""
    if "node" in data and "node_version" not in data:
        data["node_version"] = data.pop("node")
    return data


_MIGRATIONS = {
    0: (_migrate_v0_to_v1, "v0->v1: normalise pip_packages to dicts"),
    1: (_migrate_v1_to_v2, "v1->v2: rename 'node' to 'node_version'"),
}


def detect_version(data: Dict[str, Any]) -> int:
    """Return the schema version embedded in *data*, defaulting to 0."""
    return int(data.get("schema_version", 0))


def migrate_dict(
    data: Dict[str, Any],
    target_version: int = CURRENT_SCHEMA_VERSION,
) -> MigrationResult:
    """Apply incremental migrations to *data* up to *target_version*."""
    from envforge.serializer import snapshot_from_dict

    original_version = detect_version(data)
    steps: List[str] = []
    warnings: List[str] = []

    current = dict(data)
    v = original_version
    while v < target_version:
        fn, description = _MIGRATIONS.get(v, (None, None))
        if fn is None:
            warnings.append(f"No migration defined for version {v}; stopping.")
            break
        current = fn(current)
        steps.append(description)
        v += 1

    current["schema_version"] = v
    snapshot = snapshot_from_dict(current)
    return MigrationResult(
        snapshot=snapshot,
        original_version=original_version,
        target_version=v,
        steps_applied=steps,
        warnings=warnings,
    )


def migrate_snapshot(
    snapshot: EnvSnapshot,
    source_version: int,
    target_version: int = CURRENT_SCHEMA_VERSION,
) -> MigrationResult:
    """Convenience wrapper that accepts an already-loaded *snapshot*."""
    from envforge.serializer import snapshot_to_dict

    data = snapshot_to_dict(snapshot)
    data["schema_version"] = source_version
    return migrate_dict(data, target_version=target_version)
