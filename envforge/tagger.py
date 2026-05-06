"""Tag and label snapshots for easier organization and retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_TAGS_FILE = ".envforge_tags.json"


def get_tags_file(directory: Optional[str] = None) -> Path:
    """Return the path to the tags index file."""
    base = Path(directory) if directory else Path.home() / ".envforge"
    base.mkdir(parents=True, exist_ok=True)
    return base / DEFAULT_TAGS_FILE


def _load_index(tags_file: Path) -> Dict[str, List[str]]:
    """Load the tag index mapping snapshot_id -> list of tags."""
    if not tags_file.exists():
        return {}
    with tags_file.open("r") as f:
        return json.load(f)


def _save_index(tags_file: Path, index: Dict[str, List[str]]) -> None:
    """Persist the tag index to disk."""
    with tags_file.open("w") as f:
        json.dump(index, f, indent=2)


def add_tags(snapshot_id: str, tags: List[str], directory: Optional[str] = None) -> List[str]:
    """Add one or more tags to a snapshot. Returns the updated tag list."""
    tags_file = get_tags_file(directory)
    index = _load_index(tags_file)
    existing = set(index.get(snapshot_id, []))
    existing.update(tags)
    index[snapshot_id] = sorted(existing)
    _save_index(tags_file, index)
    return index[snapshot_id]


def remove_tags(snapshot_id: str, tags: List[str], directory: Optional[str] = None) -> List[str]:
    """Remove one or more tags from a snapshot. Returns the updated tag list."""
    tags_file = get_tags_file(directory)
    index = _load_index(tags_file)
    existing = set(index.get(snapshot_id, []))
    existing -= set(tags)
    index[snapshot_id] = sorted(existing)
    _save_index(tags_file, index)
    return index[snapshot_id]


def get_tags(snapshot_id: str, directory: Optional[str] = None) -> List[str]:
    """Return all tags associated with a snapshot."""
    tags_file = get_tags_file(directory)
    index = _load_index(tags_file)
    return index.get(snapshot_id, [])


def find_by_tag(tag: str, directory: Optional[str] = None) -> List[str]:
    """Return all snapshot IDs that have the given tag."""
    tags_file = get_tags_file(directory)
    index = _load_index(tags_file)
    return [sid for sid, tags in index.items() if tag in tags]


def clear_tags(snapshot_id: str, directory: Optional[str] = None) -> None:
    """Remove all tags for a snapshot."""
    tags_file = get_tags_file(directory)
    index = _load_index(tags_file)
    index.pop(snapshot_id, None)
    _save_index(tags_file, index)
