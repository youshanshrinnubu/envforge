"""Deduplicator: remove duplicate pip packages and env var keys from a snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import EnvSnapshot


@dataclass
class DeduplicateResult:
    snapshot: EnvSnapshot
    removed_packages: List[str] = field(default_factory=list)
    removed_env_keys: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.removed_packages or self.removed_env_keys)


def _copy_snapshot(snapshot: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        env_vars=dict(snapshot.env_vars),
        python_version=snapshot.python_version,
        node_version=snapshot.node_version,
        pip_packages=list(snapshot.pip_packages),
        label=snapshot.label,
    )


def deduplicate_pip_packages(snapshot: EnvSnapshot) -> DeduplicateResult:
    """Remove duplicate pip package entries, keeping the last occurrence."""
    seen: dict[str, int] = {}
    for i, pkg in enumerate(snapshot.pip_packages):
        name = pkg.get("name", "").lower() if isinstance(pkg, dict) else str(pkg).lower()
        seen[name] = i

    removed: List[str] = []
    new_packages = []
    kept_indices = set(seen.values())
    for i, pkg in enumerate(snapshot.pip_packages):
        name = pkg.get("name", "").lower() if isinstance(pkg, dict) else str(pkg).lower()
        if i in kept_indices:
            new_packages.append(pkg)
        else:
            removed.append(name)

    result_snap = _copy_snapshot(snapshot)
    result_snap.pip_packages = new_packages
    return DeduplicateResult(snapshot=result_snap, removed_packages=removed)


def deduplicate_env_vars(snapshot: EnvSnapshot) -> DeduplicateResult:
    """Normalise env_vars so keys are unique (dict already enforces this,
    but detect and report any keys that differ only in case)."""
    seen_lower: dict[str, str] = {}
    removed: List[str] = []
    new_env: dict[str, str] = {}

    for key, value in snapshot.env_vars.items():
        lower = key.lower()
        if lower in seen_lower:
            removed.append(key)
        else:
            seen_lower[lower] = key
            new_env[key] = value

    result_snap = _copy_snapshot(snapshot)
    result_snap.env_vars = new_env
    return DeduplicateResult(snapshot=result_snap, removed_env_keys=removed)


def deduplicate_snapshot(snapshot: EnvSnapshot) -> DeduplicateResult:
    """Run all deduplication passes and return a combined result."""
    pkg_result = deduplicate_pip_packages(snapshot)
    env_result = deduplicate_env_vars(pkg_result.snapshot)

    return DeduplicateResult(
        snapshot=env_result.snapshot,
        removed_packages=pkg_result.removed_packages,
        removed_env_keys=env_result.removed_env_keys,
    )
