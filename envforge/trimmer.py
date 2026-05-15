"""Trimmer: remove stale or redundant fields from a snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import EnvSnapshot


@dataclass
class TrimResult:
    """Result of a trim operation."""

    snapshot: EnvSnapshot
    removed_env_vars: List[str] = field(default_factory=list)
    removed_packages: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return bool(self.removed_env_vars or self.removed_packages)


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        env_vars=dict(snap.env_vars),
        python_version=snap.python_version,
        node_version=snap.node_version,
        pip_packages=list(snap.pip_packages),
        label=snap.label,
    )


def trim_empty_env_vars(snap: EnvSnapshot) -> TrimResult:
    """Remove env vars whose value is an empty string or only whitespace."""
    out = _copy_snapshot(snap)
    removed: List[str] = []
    for key, value in snap.env_vars.items():
        if not str(value).strip():
            removed.append(key)
    for key in removed:
        del out.env_vars[key]
    msgs = [f"Removed empty env var: {k}" for k in removed]
    return TrimResult(snapshot=out, removed_env_vars=removed, messages=msgs)


def trim_packages_without_version(snap: EnvSnapshot) -> TrimResult:
    """Remove pip packages that have no version pinned (version is empty/None)."""
    out = _copy_snapshot(snap)
    removed: List[str] = []
    kept = []
    for pkg in snap.pip_packages:
        if isinstance(pkg, dict):
            version = pkg.get("version", "") or ""
            if not str(version).strip():
                removed.append(pkg.get("name", str(pkg)))
            else:
                kept.append(pkg)
        else:
            kept.append(pkg)
    out.pip_packages = kept
    msgs = [f"Removed unpinned package: {n}" for n in removed]
    return TrimResult(snapshot=out, removed_packages=removed, messages=msgs)


def trim_snapshot(snap: EnvSnapshot) -> TrimResult:
    """Apply all trim passes and return a combined TrimResult."""
    r1 = trim_empty_env_vars(snap)
    r2 = trim_packages_without_version(r1.snapshot)
    return TrimResult(
        snapshot=r2.snapshot,
        removed_env_vars=r1.removed_env_vars,
        removed_packages=r2.removed_packages,
        messages=r1.messages + r2.messages,
    )
