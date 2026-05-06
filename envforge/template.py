"""Template management for envforge: save and load named snapshot templates."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List, Optional

from envforge.serializer import save_snapshot, load_snapshot
from envforge.snapshot import EnvSnapshot

DEFAULT_TEMPLATE_DIR = Path.home() / ".envforge" / "templates"


def get_template_dir(template_dir: Optional[Path] = None) -> Path:
    """Return the template directory, creating it if necessary."""
    directory = Path(template_dir) if template_dir else DEFAULT_TEMPLATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def template_path(name: str, template_dir: Optional[Path] = None) -> Path:
    """Return the file path for a named template."""
    return get_template_dir(template_dir) / f"{name}.json"


def save_template(name: str, snapshot: EnvSnapshot, template_dir: Optional[Path] = None) -> Path:
    """Save a snapshot as a named template. Returns the path written."""
    if not name or "/" in name or "\\" in name:
        raise ValueError(f"Invalid template name: {name!r}")
    path = template_path(name, template_dir)
    save_snapshot(snapshot, path)
    return path


def load_template(name: str, template_dir: Optional[Path] = None) -> EnvSnapshot:
    """Load a named template snapshot."""
    path = template_path(name, template_dir)
    if not path.exists():
        raise FileNotFoundError(f"Template {name!r} not found at {path}")
    return load_snapshot(path)


def list_templates(template_dir: Optional[Path] = None) -> List[str]:
    """Return a sorted list of available template names."""
    directory = get_template_dir(template_dir)
    return sorted(p.stem for p in directory.glob("*.json"))


def delete_template(name: str, template_dir: Optional[Path] = None) -> bool:
    """Delete a named template. Returns True if deleted, False if not found."""
    path = template_path(name, template_dir)
    if path.exists():
        path.unlink()
        return True
    return False
