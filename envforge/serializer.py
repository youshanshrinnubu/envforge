"""Serialize and deserialize EnvSnapshot objects to/from JSON."""

import json
from pathlib import Path
from envforge.snapshot import EnvSnapshot


SNAPSHOT_VERSION = "1.0"


def snapshot_to_dict(snapshot: EnvSnapshot) -> dict:
    """Convert an EnvSnapshot to a plain dictionary."""
    return {
        "version": SNAPSHOT_VERSION,
        "shell": snapshot.shell,
        "working_directory": snapshot.working_directory,
        "python_version": snapshot.python_version,
        "node_version": snapshot.node_version,
        "env_vars": snapshot.env_vars,
        "installed_packages": snapshot.installed_packages,
    }


def snapshot_from_dict(data: dict) -> EnvSnapshot:
    """Reconstruct an EnvSnapshot from a plain dictionary."""
    version = data.get("version")
    if version != SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version: {version!r}. Expected {SNAPSHOT_VERSION!r}."
        )
    return EnvSnapshot(
        shell=data["shell"],
        working_directory=data.get("working_directory", ""),
        python_version=data.get("python_version"),
        node_version=data.get("node_version"),
        env_vars=data.get("env_vars", {}),
        installed_packages=data.get("installed_packages", []),
    )


def save_snapshot(snapshot: EnvSnapshot, path: str | Path) -> None:
    """Serialize an EnvSnapshot to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(snapshot_to_dict(snapshot), f, indent=2)


def load_snapshot(path: str | Path) -> EnvSnapshot:
    """Load and deserialize an EnvSnapshot from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return snapshot_from_dict(data)
