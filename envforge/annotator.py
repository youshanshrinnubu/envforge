"""Snapshot annotation: attach, update, and retrieve free-form notes on snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from envforge.serializer import load_snapshot, save_snapshot
from envforge.snapshot import EnvSnapshot


@dataclass
class Annotation:
    text: str
    author: str = "unknown"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"text": self.text, "author": self.author, "created_at": self.created_at}

    @staticmethod
    def from_dict(d: dict) -> "Annotation":
        return Annotation(
            text=d.get("text", ""),
            author=d.get("author", "unknown"),
            created_at=d.get("created_at", ""),
        )


def get_annotations(snapshot: EnvSnapshot) -> List[Annotation]:
    """Return all annotations stored in the snapshot's extra metadata."""
    raw = (snapshot.extra or {}).get("annotations", [])
    return [Annotation.from_dict(a) for a in raw]


def add_annotation(
    snapshot: EnvSnapshot, text: str, author: str = "unknown"
) -> Annotation:
    """Append a new annotation to the snapshot and return it."""
    if snapshot.extra is None:
        snapshot.extra = {}
    annotations = snapshot.extra.setdefault("annotations", [])
    note = Annotation(text=text, author=author)
    annotations.append(note.to_dict())
    return note


def remove_annotation(snapshot: EnvSnapshot, index: int) -> bool:
    """Remove annotation at *index*. Returns True if removed, False if out of range."""
    annotations = (snapshot.extra or {}).get("annotations", [])
    if index < 0 or index >= len(annotations):
        return False
    annotations.pop(index)
    return True


def clear_annotations(snapshot: EnvSnapshot) -> int:
    """Remove all annotations. Returns the count that were deleted."""
    annotations = (snapshot.extra or {}).get("annotations", [])
    count = len(annotations)
    annotations.clear()
    return count


def annotate_file(
    path: str, text: str, author: str = "unknown"
) -> Optional[Annotation]:
    """Load a snapshot file, add an annotation, save it, and return the new annotation."""
    snapshot = load_snapshot(path)
    note = add_annotation(snapshot, text, author)
    save_snapshot(snapshot, path)
    return note
