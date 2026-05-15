"""Filter snapshots by env vars, packages, or metadata criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class FilterResult:
    """Result of a filter operation."""
    original_env_count: int
    original_pkg_count: int
    filtered_env_count: int
    filtered_pkg_count: int
    snapshot: EnvSnapshot
    applied_filters: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return (
            self.filtered_env_count < self.original_env_count
            or self.filtered_pkg_count < self.original_pkg_count
        )


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    import copy
    return copy.deepcopy(snap)


def filter_env_vars(
    snap: EnvSnapshot,
    predicate: Callable[[str, str], bool],
) -> FilterResult:
    """Keep only env vars where predicate(key, value) is True."""
    original = dict(snap.env_vars)
    result = _copy_snapshot(snap)
    result.env_vars = {k: v for k, v in original.items() if predicate(k, v)}
    return FilterResult(
        original_env_count=len(original),
        original_pkg_count=len(snap.pip_packages),
        filtered_env_count=len(result.env_vars),
        filtered_pkg_count=len(result.pip_packages),
        snapshot=result,
        applied_filters=["env_vars"],
    )


def filter_pip_packages(
    snap: EnvSnapshot,
    predicate: Callable[[dict], bool],
) -> FilterResult:
    """Keep only pip packages where predicate(pkg_dict) is True."""
    original = list(snap.pip_packages)
    result = _copy_snapshot(snap)
    result.pip_packages = [p for p in original if predicate(p)]
    return FilterResult(
        original_env_count=len(snap.env_vars),
        original_pkg_count=len(original),
        filtered_env_count=len(result.env_vars),
        filtered_pkg_count=len(result.pip_packages),
        snapshot=result,
        applied_filters=["pip_packages"],
    )


def filter_snapshot(
    snap: EnvSnapshot,
    env_predicate: Optional[Callable[[str, str], bool]] = None,
    pkg_predicate: Optional[Callable[[dict], bool]] = None,
) -> FilterResult:
    """Apply both env var and package filters in one call."""
    original_env = len(snap.env_vars)
    original_pkg = len(snap.pip_packages)
    applied: List[str] = []

    result = _copy_snapshot(snap)

    if env_predicate is not None:
        result.env_vars = {k: v for k, v in result.env_vars.items() if env_predicate(k, v)}
        applied.append("env_vars")

    if pkg_predicate is not None:
        result.pip_packages = [p for p in result.pip_packages if pkg_predicate(p)]
        applied.append("pip_packages")

    return FilterResult(
        original_env_count=original_env,
        original_pkg_count=original_pkg,
        filtered_env_count=len(result.env_vars),
        filtered_pkg_count=len(result.pip_packages),
        snapshot=result,
        applied_filters=applied,
    )
