"""Snapshot quality scorer — assigns a numeric score to a snapshot based on completeness and best practices."""

from dataclasses import dataclass, field
from typing import List
from envforge.snapshot import EnvSnapshot

MAX_SCORE = 100


@dataclass
class ScoreResult:
    score: int
    max_score: int = MAX_SCORE
    breakdown: dict = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        pct = self.score / self.max_score
        if pct >= 0.9:
            return "A"
        if pct >= 0.75:
            return "B"
        if pct >= 0.6:
            return "C"
        if pct >= 0.4:
            return "D"
        return "F"

    @property
    def percentage(self) -> float:
        return round(100.0 * self.score / self.max_score, 1)


def _score_python_version(snapshot: EnvSnapshot) -> tuple[int, str | None]:
    """Up to 20 points for having a pinned Python version."""
    if not snapshot.python_version:
        return 0, "Add a Python version to improve reproducibility."
    parts = snapshot.python_version.split(".")
    if len(parts) >= 3:
        return 20, None
    return 10, "Pin Python version to patch level (e.g. 3.11.4) for full points."


def _score_pip_packages(snapshot: EnvSnapshot) -> tuple[int, str | None]:
    """Up to 30 points for pinned pip packages."""
    pkgs = snapshot.pip_packages or {}
    if not pkgs:
        return 0, "No pip packages recorded; consider running inside a virtualenv."
    pinned = sum(1 for v in pkgs.values() if v and v != "*")
    ratio = pinned / len(pkgs)
    score = round(ratio * 30)
    if ratio < 1.0:
        return score, f"{len(pkgs) - pinned} package(s) lack pinned versions."
    return 30, None


def _score_env_vars(snapshot: EnvSnapshot) -> tuple[int, str | None]:
    """Up to 20 points for having env vars recorded."""
    count = len(snapshot.env_vars or {})
    if count == 0:
        return 0, "No environment variables captured."
    if count >= 5:
        return 20, None
    return 10, "Capture more environment variables for better reproducibility."


def _score_node_version(snapshot: EnvSnapshot) -> tuple[int, str | None]:
    """Up to 15 points for having a node version."""
    if snapshot.node_version:
        return 15, None
    return 0, "Node.js version not recorded (skip if not applicable)."


def _score_shell(snapshot: EnvSnapshot) -> tuple[int, str | None]:
    """Up to 15 points for shell info."""
    shell = (snapshot.env_vars or {}).get("SHELL") or (snapshot.env_vars or {}).get("shell")
    if shell:
        return 15, None
    return 5, "SHELL variable not captured; include it for full shell reproducibility."


def score_snapshot(snapshot: EnvSnapshot) -> ScoreResult:
    total = 0
    breakdown = {}
    suggestions = []

    checks = [
        ("python_version", _score_python_version),
        ("pip_packages", _score_pip_packages),
        ("env_vars", _score_env_vars),
        ("node_version", _score_node_version),
        ("shell", _score_shell),
    ]

    for key, fn in checks:
        pts, hint = fn(snapshot)
        breakdown[key] = pts
        total += pts
        if hint:
            suggestions.append(hint)

    return ScoreResult(score=total, breakdown=breakdown, suggestions=suggestions)
