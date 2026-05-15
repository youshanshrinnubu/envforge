"""splitter.py — Split a snapshot into multiple smaller snapshots by criteria."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class SplitResult:
    """Result of a snapshot split operation."""

    parts: Dict[str, EnvSnapshot] = field(default_factory=dict)
    skipped_env_vars: int = 0
    skipped_packages: int = 0

    def __bool__(self) -> bool:  # noqa: D105
        return len(self.parts) > 0


def _copy_snapshot(snapshot: EnvSnapshot, label: Optional[str] = None) -> EnvSnapshot:
    """Return a shallow-copied snapshot with an optional new label."""
    copy = EnvSnapshot(
        label=label or snapshot.label,
        env_vars=dict(snapshot.env_vars),
        python_version=snapshot.python_version,
        node_version=snapshot.node_version,
        pip_packages=list(snapshot.pip_packages),
        extra=dict(snapshot.extra),
    )
    return copy


def split_by_env_prefix(
    snapshot: EnvSnapshot,
    prefixes: List[str],
    include_unmatched: bool = True,
) -> SplitResult:
    """Split env_vars into groups based on key prefix.

    Each prefix becomes a separate snapshot part keyed by the prefix string.
    Unmatched vars go into an ``"other"`` part when *include_unmatched* is True.
    """
    result = SplitResult()
    buckets: Dict[str, dict] = {p: {} for p in prefixes}
    other: dict = {}

    for key, value in snapshot.env_vars.items():
        matched = False
        for prefix in prefixes:
            if key.startswith(prefix):
                buckets[prefix][key] = value
                matched = True
                break
        if not matched:
            if include_unmatched:
                other[key] = value
            else:
                result.skipped_env_vars += 1

    for prefix, vars_dict in buckets.items():
        part = _copy_snapshot(snapshot, label=f"{snapshot.label or 'snapshot'}_{prefix.rstrip('_').lower()}")
        part.env_vars = vars_dict
        part.pip_packages = []
        result.parts[prefix] = part

    if include_unmatched and other:
        other_part = _copy_snapshot(snapshot, label=f"{snapshot.label or 'snapshot'}_other")
        other_part.env_vars = other
        other_part.pip_packages = []
        result.parts["other"] = other_part

    return result


def split_by_package_prefix(
    snapshot: EnvSnapshot,
    prefixes: List[str],
    include_unmatched: bool = True,
) -> SplitResult:
    """Split pip_packages into groups based on package-name prefix."""
    result = SplitResult()
    buckets: Dict[str, list] = {p: [] for p in prefixes}
    other: list = []

    for pkg in snapshot.pip_packages:
        name = pkg.get("name", "") if isinstance(pkg, dict) else str(pkg)
        matched = False
        for prefix in prefixes:
            if name.lower().startswith(prefix.lower()):
                buckets[prefix].append(pkg)
                matched = True
                break
        if not matched:
            if include_unmatched:
                other.append(pkg)
            else:
                result.skipped_packages += 1

    for prefix, pkgs in buckets.items():
        part = _copy_snapshot(snapshot, label=f"{snapshot.label or 'snapshot'}_{prefix.lower()}")
        part.env_vars = {}
        part.pip_packages = pkgs
        result.parts[prefix] = part

    if include_unmatched and other:
        other_part = _copy_snapshot(snapshot, label=f"{snapshot.label or 'snapshot'}_other")
        other_part.env_vars = {}
        other_part.pip_packages = other
        result.parts["other"] = other_part

    return result
