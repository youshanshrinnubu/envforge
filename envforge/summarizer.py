"""Summarizer: produce a human-readable text summary of an EnvSnapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import EnvSnapshot


@dataclass
class SnapshotSummary:
    title: str
    sections: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [f"=== {self.title} ==="]
        for section in self.sections:
            lines.append(section)
        return "\n".join(lines)


def _summarize_versions(snapshot: EnvSnapshot) -> str:
    parts = []
    if snapshot.python_version:
        parts.append(f"  Python : {snapshot.python_version}")
    if snapshot.node_version:
        parts.append(f"  Node   : {snapshot.node_version}")
    if not parts:
        return "  (no language versions recorded)"
    return "\n".join(parts)


def _summarize_env_vars(snapshot: EnvSnapshot) -> str:
    if not snapshot.env_vars:
        return "  (no environment variables)"
    lines = []
    for key in sorted(snapshot.env_vars):
        value = snapshot.env_vars[key]
        display = value if len(value) <= 40 else value[:37] + "..."
        lines.append(f"  {key}={display}")
    return "\n".join(lines)


def _summarize_pip_packages(snapshot: EnvSnapshot) -> str:
    if not snapshot.pip_packages:
        return "  (no pip packages)"
    lines = []
    for pkg in sorted(snapshot.pip_packages, key=lambda p: p.lower()):
        lines.append(f"  {pkg}")
    return "\n".join(lines)


def summarize_snapshot(snapshot: EnvSnapshot, title: str = "Snapshot Summary") -> SnapshotSummary:
    """Build a SnapshotSummary from an EnvSnapshot."""
    summary = SnapshotSummary(title=title)

    summary.sections.append("[Language Versions]")
    summary.sections.append(_summarize_versions(snapshot))

    summary.sections.append("[Environment Variables]")
    summary.sections.append(_summarize_env_vars(snapshot))

    summary.sections.append("[Pip Packages]")
    summary.sections.append(_summarize_pip_packages(snapshot))

    return summary
