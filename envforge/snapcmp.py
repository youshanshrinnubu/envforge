"""snapcmp: side-by-side snapshot comparison report."""
from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import EnvSnapshot
from envforge.differ import compare_snapshots, SnapshotDiff


@dataclass
class ComparisonReport:
    left_label: str
    right_label: str
    diff: SnapshotDiff
    summary_lines: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """True when the two snapshots are identical."""
        from envforge.differ import has_differences
        return not has_differences(self.diff)

    def __str__(self) -> str:
        lines = [
            f"Comparison: [{self.left_label}] vs [{self.right_label}]",
            "-" * 60,
        ]
        lines.extend(self.summary_lines)
        if not self.summary_lines:
            lines.append("  No differences found.")
        return "\n".join(lines)


def _fmt_env_section(diff: SnapshotDiff) -> List[str]:
    lines = []
    for k, v in diff.env_added.items():
        lines.append(f"  ENV  + {k}={v}")
    for k, v in diff.env_removed.items():
        lines.append(f"  ENV  - {k}={v}")
    for k, (old, new) in diff.env_changed.items():
        lines.append(f"  ENV  ~ {k}: {old!r} -> {new!r}")
    return lines


def _fmt_pkg_section(diff: SnapshotDiff) -> List[str]:
    lines = []
    for pkg, ver in diff.pip_added.items():
        lines.append(f"  PKG  + {pkg}=={ver}")
    for pkg, ver in diff.pip_removed.items():
        lines.append(f"  PKG  - {pkg}=={ver}")
    for pkg, (old, new) in diff.pip_changed.items():
        lines.append(f"  PKG  ~ {pkg}: {old} -> {new}")
    return lines


def _fmt_version_section(diff: SnapshotDiff) -> List[str]:
    lines = []
    if diff.python_version_changed:
        old, new = diff.python_version_changed
        lines.append(f"  PY   ~ python: {old} -> {new}")
    if diff.node_version_changed:
        old, new = diff.node_version_changed
        lines.append(f"  NODE ~ node: {old} -> {new}")
    return lines


def compare_snapshots_report(
    left: EnvSnapshot,
    right: EnvSnapshot,
    left_label: Optional[str] = None,
    right_label: Optional[str] = None,
) -> ComparisonReport:
    """Produce a ComparisonReport between two snapshots."""
    diff = compare_snapshots(left, right)
    lbl_l = left_label or left.label or "snapshot-A"
    lbl_r = right_label or right.label or "snapshot-B"
    summary: List[str] = []
    summary.extend(_fmt_version_section(diff))
    summary.extend(_fmt_env_section(diff))
    summary.extend(_fmt_pkg_section(diff))
    return ComparisonReport(
        left_label=lbl_l,
        right_label=lbl_r,
        diff=diff,
        summary_lines=summary,
    )
