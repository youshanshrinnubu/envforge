"""Normalize snapshot fields for consistent comparison and storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envforge.snapshot import EnvSnapshot


@dataclass
class NormalizeResult:
    snapshot: EnvSnapshot
    changes: list[str] = field(default_factory=list)
    original_count: int = 0
    normalized_count: int = 0

    def __bool__(self) -> bool:
        return len(self.changes) > 0


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    import copy
    return copy.deepcopy(snap)


def normalize_env_var_keys(snap: EnvSnapshot) -> NormalizeResult:
    """Upper-case all environment variable keys."""
    result = _copy_snapshot(snap)
    changes: list[str] = []
    new_env: dict[str, str] = {}
    for k, v in (snap.env_vars or {}).items():
        upper = k.upper()
        if upper != k:
            changes.append(f"env_var key: {k!r} -> {upper!r}")
        new_env[upper] = v
    result.env_vars = new_env
    return NormalizeResult(
        snapshot=result,
        changes=changes,
        original_count=len(snap.env_vars or {}),
        normalized_count=len(new_env),
    )


def normalize_package_names(snap: EnvSnapshot) -> NormalizeResult:
    """Lower-case all pip package names and strip whitespace."""
    result = _copy_snapshot(snap)
    changes: list[str] = []
    new_pkgs: list[dict[str, Any]] = []
    for pkg in snap.pip_packages or []:
        name = pkg.get("name", "")
        normalized = name.strip().lower().replace("_", "-")
        if normalized != name:
            changes.append(f"package name: {name!r} -> {normalized!r}")
        new_pkgs.append({**pkg, "name": normalized})
    result.pip_packages = new_pkgs
    return NormalizeResult(
        snapshot=result,
        changes=changes,
        original_count=len(snap.pip_packages or []),
        normalized_count=len(new_pkgs),
    )


def normalize_snapshot(snap: EnvSnapshot) -> NormalizeResult:
    """Apply all normalization passes to a snapshot."""
    env_result = normalize_env_var_keys(snap)
    pkg_result = normalize_package_names(env_result.snapshot)
    all_changes = env_result.changes + pkg_result.changes
    return NormalizeResult(
        snapshot=pkg_result.snapshot,
        changes=all_changes,
        original_count=env_result.original_count + pkg_result.original_count,
        normalized_count=env_result.normalized_count + pkg_result.normalized_count,
    )
