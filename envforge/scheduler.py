"""Snapshot scheduling: define and run periodic auto-capture jobs."""

import json
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

DEFAULT_SCHEDULE_FILE = os.path.expanduser("~/.envforge/schedule.json")


@dataclass
class ScheduleEntry:
    name: str
    interval_seconds: int
    output_dir: str
    last_run: Optional[float] = None
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


def _load_schedule(path: str = DEFAULT_SCHEDULE_FILE) -> List[ScheduleEntry]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        raw = json.load(f)
    return [
        ScheduleEntry(
            name=e["name"],
            interval_seconds=e["interval_seconds"],
            output_dir=e["output_dir"],
            last_run=e.get("last_run"),
            enabled=e.get("enabled", True),
            tags=e.get("tags", []),
        )
        for e in raw
    ]


def _save_schedule(entries: List[ScheduleEntry], path: str = DEFAULT_SCHEDULE_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(
            [
                {
                    "name": e.name,
                    "interval_seconds": e.interval_seconds,
                    "output_dir": e.output_dir,
                    "last_run": e.last_run,
                    "enabled": e.enabled,
                    "tags": e.tags,
                }
                for e in entries
            ],
            f,
            indent=2,
        )


def add_schedule(name: str, interval_seconds: int, output_dir: str,
                 tags: Optional[List[str]] = None,
                 path: str = DEFAULT_SCHEDULE_FILE) -> ScheduleEntry:
    entries = _load_schedule(path)
    if any(e.name == name for e in entries):
        raise ValueError(f"Schedule '{name}' already exists.")
    entry = ScheduleEntry(name=name, interval_seconds=interval_seconds,
                          output_dir=output_dir, tags=tags or [])
    entries.append(entry)
    _save_schedule(entries, path)
    return entry


def remove_schedule(name: str, path: str = DEFAULT_SCHEDULE_FILE) -> bool:
    entries = _load_schedule(path)
    new_entries = [e for e in entries if e.name != name]
    if len(new_entries) == len(entries):
        return False
    _save_schedule(new_entries, path)
    return True


def list_schedules(path: str = DEFAULT_SCHEDULE_FILE) -> List[ScheduleEntry]:
    return _load_schedule(path)


def due_schedules(path: str = DEFAULT_SCHEDULE_FILE) -> List[ScheduleEntry]:
    now = time.time()
    return [
        e for e in _load_schedule(path)
        if e.enabled and (e.last_run is None or now - e.last_run >= e.interval_seconds)
    ]


def mark_ran(name: str, path: str = DEFAULT_SCHEDULE_FILE) -> None:
    entries = _load_schedule(path)
    for e in entries:
        if e.name == name:
            e.last_run = time.time()
    _save_schedule(entries, path)
