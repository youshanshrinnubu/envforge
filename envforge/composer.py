"""Snapshot composer: merge multiple snapshots into one unified snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class ComposeResult:
    snapshot: Optional[EnvSnapshot]
    source_labels: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.snapshot is not None


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        label=snap.label,
        python_version=snap.python_version,
        node_version=snap.node_version,
        env_vars=dict(snap.env_vars),
        pip_packages=list(snap.pip_packages),
        extra=dict(snap.extra) if snap.extra else {},
    )


def compose_snapshots(
    snapshots: List[EnvSnapshot],
    label: Optional[str] = None,
    prefer_last: bool = True,
) -> ComposeResult:
    """Compose a list of snapshots into a single unified snapshot.

    Later snapshots in the list override earlier ones when *prefer_last* is
    True (default).  Conflicts are recorded but do not block composition.
    """
    if not snapshots:
        return ComposeResult(snapshot=None, warnings=["No snapshots provided"])

    base = _copy_snapshot(snapshots[0])
    source_labels = [s.label or "(unlabeled)" for s in snapshots]
    conflicts: List[str] = []

    for snap in snapshots[1:]:
        # Merge env vars
        for key, value in snap.env_vars.items():
            if key in base.env_vars and base.env_vars[key] != value:
                conflicts.append(f"env_var:{key}")
            if prefer_last or key not in base.env_vars:
                base.env_vars[key] = value

        # Merge pip packages (by package name)
        existing_names = {}
        for i, pkg in enumerate(base.pip_packages):
            name = pkg.get("name") if isinstance(pkg, dict) else str(pkg)
            if name:
                existing_names[name.lower()] = i

        for pkg in snap.pip_packages:
            name = pkg.get("name") if isinstance(pkg, dict) else str(pkg)
            key = (name or "").lower()
            if key in existing_names:
                existing_pkg = base.pip_packages[existing_names[key]]
                old_ver = existing_pkg.get("version") if isinstance(existing_pkg, dict) else None
                new_ver = pkg.get("version") if isinstance(pkg, dict) else None
                if old_ver != new_ver:
                    conflicts.append(f"pip:{name}")
                if prefer_last:
                    base.pip_packages[existing_names[key]] = pkg
            else:
                existing_names[key] = len(base.pip_packages)
                base.pip_packages.append(pkg)

        # Prefer last for runtime versions
        if snap.python_version and (prefer_last or not base.python_version):
            base.python_version = snap.python_version
        if snap.node_version and (prefer_last or not base.node_version):
            base.node_version = snap.node_version

    if label is not None:
        base.label = label

    return ComposeResult(
        snapshot=base,
        source_labels=source_labels,
        conflicts=list(dict.fromkeys(conflicts)),  # deduplicate, preserve order
    )
