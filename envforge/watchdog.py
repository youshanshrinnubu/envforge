"""envforge.watchdog — detect drift between a saved snapshot and the live environment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envforge.comparator import compare_with_live, LiveComparison
from envforge.snapshot import EnvSnapshot
from envforge.notifier import load_config, notify


@dataclass
class DriftReport:
    snapshot_label: str
    has_drift: bool
    added_env_vars: list[str] = field(default_factory=list)
    removed_env_vars: list[str] = field(default_factory=list)
    changed_env_vars: list[str] = field(default_factory=list)
    added_packages: list[str] = field(default_factory=list)
    removed_packages: list[str] = field(default_factory=list)
    changed_packages: list[str] = field(default_factory=list)
    python_version_changed: bool = False
    summary: str = ""

    def __bool__(self) -> bool:
        return self.has_drift


def _build_summary(report: DriftReport) -> str:
    parts: list[str] = []
    if report.python_version_changed:
        parts.append("python version changed")
    total_env = len(report.added_env_vars) + len(report.removed_env_vars) + len(report.changed_env_vars)
    if total_env:
        parts.append(f"{total_env} env-var change(s)")
    total_pkg = len(report.added_packages) + len(report.removed_packages) + len(report.changed_packages)
    if total_pkg:
        parts.append(f"{total_pkg} package change(s)")
    if not parts:
        return "no drift detected"
    return "; ".join(parts)


def detect_drift(
    snapshot: EnvSnapshot,
    *,
    notify_on_drift: bool = False,
    config_path: Optional[str] = None,
) -> DriftReport:
    """Compare *snapshot* against the live environment and return a DriftReport."""
    comparison: LiveComparison = compare_with_live(snapshot)
    diff = comparison.diff

    report = DriftReport(
        snapshot_label=snapshot.label or "(unlabeled)",
        has_drift=not comparison.is_clean,
        added_env_vars=list(diff.env_vars.added),
        removed_env_vars=list(diff.env_vars.removed),
        changed_env_vars=list(diff.env_vars.changed),
        added_packages=list(diff.pip_packages.added),
        removed_packages=list(diff.pip_packages.removed),
        changed_packages=list(diff.pip_packages.changed),
        python_version_changed=diff.python_version_changed,
    )
    report.summary = _build_summary(report)

    if notify_on_drift and report.has_drift:
        cfg = load_config(config_path) if config_path else load_config()
        notify(cfg, "drift", details={"summary": report.summary, "label": report.snapshot_label})

    return report
