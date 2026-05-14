"""Snapshot labeler: apply, remove, and query human-readable labels on snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class LabelResult:
    """Result of a labeling operation."""

    snapshot: EnvSnapshot
    previous_label: Optional[str]
    new_label: Optional[str]
    changed: bool

    def __bool__(self) -> bool:
        return self.changed


def get_label(snapshot: EnvSnapshot) -> Optional[str]:
    """Return the current label of *snapshot*, or None if unlabeled."""
    return getattr(snapshot, "label", None) or None


def set_label(snapshot: EnvSnapshot, label: str) -> LabelResult:
    """Set a new label on *snapshot*.

    Returns a :class:`LabelResult` describing what changed.
    """
    if not label or not label.strip():
        raise ValueError("label must be a non-empty string")

    previous = get_label(snapshot)
    snapshot.label = label.strip()
    changed = previous != snapshot.label
    return LabelResult(
        snapshot=snapshot,
        previous_label=previous,
        new_label=snapshot.label,
        changed=changed,
    )


def clear_label(snapshot: EnvSnapshot) -> LabelResult:
    """Remove the label from *snapshot*.

    Returns a :class:`LabelResult`; ``changed`` is False when there was no
    label to begin with.
    """
    previous = get_label(snapshot)
    snapshot.label = ""
    return LabelResult(
        snapshot=snapshot,
        previous_label=previous,
        new_label=None,
        changed=previous is not None,
    )


def has_label(snapshot: EnvSnapshot) -> bool:
    """Return True if *snapshot* has a non-empty label."""
    return bool(get_label(snapshot))


def label_matches(snapshot: EnvSnapshot, pattern: str) -> bool:
    """Return True if the snapshot label contains *pattern* (case-insensitive)."""
    lbl = get_label(snapshot)
    if lbl is None:
        return False
    return pattern.lower() in lbl.lower()
