"""Snapshot history tracking: save, list, and retrieve past snapshots."""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from envforge.snapshot import EnvSnapshot
from envforge.serializer import snapshot_to_dict, snapshot_from_dict

DEFAULT_HISTORY_DIR = Path.home() / ".envforge" / "history"


def get_history_dir(history_dir: Optional[Path] = None) -> Path:
    """Return the history directory, defaulting to ~/.envforge/history."""
    return Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR


def record_snapshot(snapshot: EnvSnapshot, label: Optional[str] = None,
                    history_dir: Optional[Path] = None) -> Path:
    """Save a snapshot to history with a timestamped filename."""
    hdir = get_history_dir(history_dir)
    hdir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    slug = f"{timestamp}_{label}" if label else timestamp
    filepath = hdir / f"{slug}.json"

    data = snapshot_to_dict(snapshot)
    data["_history"] = {"timestamp": timestamp, "label": label or ""}

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return filepath


def list_history(history_dir: Optional[Path] = None) -> List[dict]:
    """Return metadata for all recorded snapshots, sorted newest first."""
    hdir = get_history_dir(history_dir)
    if not hdir.exists():
        return []

    entries = []
    for path in sorted(hdir.glob("*.json"), reverse=True):
        try:
            with open(path) as f:
                data = json.load(f)
            meta = data.get("_history", {})
            entries.append({
                "filename": path.name,
                "path": str(path),
                "timestamp": meta.get("timestamp", ""),
                "label": meta.get("label", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return entries


def load_history_entry(filename: str,
                       history_dir: Optional[Path] = None) -> EnvSnapshot:
    """Load a snapshot from history by filename."""
    hdir = get_history_dir(history_dir)
    filepath = hdir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"History entry not found: {filename}")

    with open(filepath) as f:
        data = json.load(f)

    data.pop("_history", None)
    return snapshot_from_dict(data)


def delete_history_entry(filename: str,
                         history_dir: Optional[Path] = None) -> None:
    """Delete a snapshot history entry by filename."""
    hdir = get_history_dir(history_dir)
    filepath = hdir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"History entry not found: {filename}")
    filepath.unlink()
