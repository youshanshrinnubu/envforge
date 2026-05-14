"""Transform snapshots by applying field-level mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class TransformResult:
    snapshot: EnvSnapshot
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return len(self.applied) > 0


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    """Return a shallow copy of a snapshot."""
    return EnvSnapshot(
        label=snap.label,
        python_version=snap.python_version,
        node_version=snap.node_version,
        env_vars=dict(snap.env_vars),
        pip_packages=list(snap.pip_packages),
        shell=snap.shell,
        os_info=snap.os_info,
    )


def transform_env_vars(
    snapshot: EnvSnapshot,
    transformer: Callable[[str, str], Optional[str]],
) -> TransformResult:
    """Apply *transformer* to every env var; returning None drops the key."""
    result = _copy_snapshot(snapshot)
    applied, skipped = [], []
    new_vars: Dict[str, str] = {}
    for k, v in snapshot.env_vars.items():
        new_val = transformer(k, v)
        if new_val is None:
            skipped.append(k)
        else:
            new_vars[k] = new_val
            if new_val != v:
                applied.append(k)
    result.env_vars = new_vars
    return TransformResult(snapshot=result, applied=applied, skipped=skipped)


def transform_pip_packages(
    snapshot: EnvSnapshot,
    transformer: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
) -> TransformResult:
    """Apply *transformer* to every pip package entry; None removes it."""
    result = _copy_snapshot(snapshot)
    applied, skipped = [], []
    new_pkgs = []
    for pkg in snapshot.pip_packages:
        new_pkg = transformer(pkg)
        name = pkg.get("name", str(pkg))
        if new_pkg is None:
            skipped.append(name)
        else:
            new_pkgs.append(new_pkg)
            if new_pkg != pkg:
                applied.append(name)
    result.pip_packages = new_pkgs
    return TransformResult(snapshot=result, applied=applied, skipped=skipped)


def apply_transforms(
    snapshot: EnvSnapshot,
    env_transformer: Optional[Callable[[str, str], Optional[str]]] = None,
    pkg_transformer: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None,
) -> TransformResult:
    """Convenience wrapper applying both optional transformers in sequence."""
    current = snapshot
    all_applied: List[str] = []
    all_skipped: List[str] = []

    if env_transformer is not None:
        r = transform_env_vars(current, env_transformer)
        current = r.snapshot
        all_applied.extend(r.applied)
        all_skipped.extend(r.skipped)

    if pkg_transformer is not None:
        r = transform_pip_packages(current, pkg_transformer)
        current = r.snapshot
        all_applied.extend(r.applied)
        all_skipped.extend(r.skipped)

    return TransformResult(snapshot=current, applied=all_applied, skipped=all_skipped)
