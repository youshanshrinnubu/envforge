"""Merge two snapshots, with configurable conflict resolution strategies."""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from envforge.snapshot import EnvSnapshot

ConflictStrategy = Literal["prefer_base", "prefer_other", "union"]


@dataclass
class MergeResult:
    snapshot: EnvSnapshot
    conflicts: Dict[str, tuple] = field(default_factory=dict)  # key -> (base_val, other_val)
    notes: List[str] = field(default_factory=list)


def merge_env_vars(
    base: Dict[str, str],
    other: Dict[str, str],
    strategy: ConflictStrategy = "prefer_other",
) -> tuple[Dict[str, str], Dict[str, tuple]]:
    """Merge two env var dicts. Returns merged dict and conflict map."""
    merged = dict(base)
    conflicts: Dict[str, tuple] = {}

    for key, value in other.items():
        if key in merged and merged[key] != value:
            conflicts[key] = (merged[key], value)
            if strategy == "prefer_other":
                merged[key] = value
            # prefer_base: keep existing value (no-op)
        else:
            merged[key] = value

    return merged, conflicts


def merge_pip_packages(
    base: Dict[str, str],
    other: Dict[str, str],
    strategy: ConflictStrategy = "prefer_other",
) -> tuple[Dict[str, str], Dict[str, tuple]]:
    """Merge pip package dicts. Returns merged dict and version conflict map."""
    merged = dict(base)
    conflicts: Dict[str, tuple] = {}

    for pkg, version in other.items():
        if pkg in merged and merged[pkg] != version:
            conflicts[pkg] = (merged[pkg], version)
            if strategy == "prefer_other":
                merged[pkg] = version
        else:
            merged[pkg] = version

    return merged, conflicts


def merge_snapshots(
    base: EnvSnapshot,
    other: EnvSnapshot,
    strategy: ConflictStrategy = "prefer_other",
    label: Optional[str] = None,
) -> MergeResult:
    """Merge two EnvSnapshot objects into a new snapshot."""
    merged_env, env_conflicts = merge_env_vars(base.env_vars, other.env_vars, strategy)
    merged_pip, pip_conflicts = merge_pip_packages(
        base.pip_packages, other.pip_packages, strategy
    )

    # Resolve version strings
    python_version = (
        other.python_version
        if strategy == "prefer_other" and other.python_version
        else base.python_version
    )
    node_version = (
        other.node_version
        if strategy == "prefer_other" and other.node_version
        else base.node_version
    )

    merged_snapshot = EnvSnapshot(
        env_vars=merged_env,
        python_version=python_version,
        node_version=node_version,
        pip_packages=merged_pip,
        label=label or f"merged({base.label or 'base'}, {other.label or 'other'})",
    )

    all_conflicts = {**{f"env:{k}": v for k, v in env_conflicts.items()},
                     **{f"pip:{k}": v for k, v in pip_conflicts.items()}}

    notes = []
    if env_conflicts:
        notes.append(f"{len(env_conflicts)} env var conflict(s) resolved via '{strategy}'")
    if pip_conflicts:
        notes.append(f"{len(pip_conflicts)} pip package conflict(s) resolved via '{strategy}'")

    return MergeResult(snapshot=merged_snapshot, conflicts=all_conflicts, notes=notes)
