"""Compare two environment snapshots and report differences."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from envforge.snapshot import EnvSnapshot


@dataclass
class SnapshotDiff:
    env_added: Dict[str, str] = field(default_factory=dict)
    env_removed: Dict[str, str] = field(default_factory=dict)
    env_changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    pip_added: List[str] = field(default_factory=list)
    pip_removed: List[str] = field(default_factory=list)
    pip_changed: List[Tuple[str, str, str]] = field(default_factory=list)
    python_version_changed: Optional[Tuple[str, str]] = None
    node_version_changed: Optional[Tuple[str, str]] = None

    def has_differences(self) -> bool:
        return any([
            self.env_added,
            self.env_removed,
            self.env_changed,
            self.pip_added,
            self.pip_removed,
            self.pip_changed,
            self.python_version_changed is not None,
            self.node_version_changed is not None,
        ])


def diff_env_vars(
    base: Dict[str, str], other: Dict[str, str]
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Tuple[str, str]]]:
    added = {k: v for k, v in other.items() if k not in base}
    removed = {k: v for k, v in base.items() if k not in other}
    changed = {
        k: (base[k], other[k])
        for k in base
        if k in other and base[k] != other[k]
    }
    return added, removed, changed


def diff_pip_packages(
    base: Dict[str, str], other: Dict[str, str]
) -> Tuple[List[str], List[str], List[Tuple[str, str, str]]]:
    added = [f"{k}=={v}" for k, v in other.items() if k not in base]
    removed = [f"{k}=={v}" for k, v in base.items() if k not in other]
    changed = [
        (k, base[k], other[k])
        for k in base
        if k in other and base[k] != other[k]
    ]
    return added, removed, changed


def compare_snapshots(base: EnvSnapshot, other: EnvSnapshot) -> SnapshotDiff:
    diff = SnapshotDiff()

    diff.env_added, diff.env_removed, diff.env_changed = diff_env_vars(
        base.env_vars, other.env_vars
    )

    base_pip = {p.split("==")[0]: p.split("==")[1] for p in base.pip_packages if "==" in p}
    other_pip = {p.split("==")[0]: p.split("==")[1] for p in other.pip_packages if "==" in p}
    diff.pip_added, diff.pip_removed, diff.pip_changed = diff_pip_packages(base_pip, other_pip)

    if base.python_version != other.python_version:
        diff.python_version_changed = (base.python_version, other.python_version)

    if base.node_version != other.node_version:
        diff.node_version_changed = (base.node_version, other.node_version)

    return diff


def format_diff(diff: SnapshotDiff) -> str:
    lines = []
    if diff.python_version_changed:
        lines.append(f"[python] {diff.python_version_changed[0]} -> {diff.python_version_changed[1]}")
    if diff.node_version_changed:
        lines.append(f"[node]   {diff.node_version_changed[0]} -> {diff.node_version_changed[1]}")
    for k, v in diff.env_added.items():
        lines.append(f"[env +]  {k}={v}")
    for k, v in diff.env_removed.items():
        lines.append(f"[env -]  {k}={v}")
    for k, (old, new) in diff.env_changed.items():
        lines.append(f"[env ~]  {k}: {old} -> {new}")
    for pkg in diff.pip_added:
        lines.append(f"[pip +]  {pkg}")
    for pkg in diff.pip_removed:
        lines.append(f"[pip -]  {pkg}")
    for name, old, new in diff.pip_changed:
        lines.append(f"[pip ~]  {name}: {old} -> {new}")
    return "\n".join(lines) if lines else "No differences found."
