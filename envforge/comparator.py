"""Compare a snapshot against the current live environment."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List

from envforge.snapshot import EnvSnapshot, capture_env_vars, capture_pip_packages


@dataclass
class LiveComparison:
    """Result of comparing a snapshot against the live environment."""

    missing_env_vars: List[str] = field(default_factory=list)
    changed_env_vars: Dict[str, tuple] = field(default_factory=dict)  # key -> (snapshot, live)
    extra_env_vars: List[str] = field(default_factory=list)

    missing_packages: List[str] = field(default_factory=list)
    changed_packages: Dict[str, tuple] = field(default_factory=dict)  # name -> (snapshot, live)
    extra_packages: List[str] = field(default_factory=list)

    python_match: bool = True
    snapshot_python: str = ""
    live_python: str = ""

    @property
    def is_clean(self) -> bool:
        """Return True when the live environment matches the snapshot exactly."""
        return (
            not self.missing_env_vars
            and not self.changed_env_vars
            and not self.extra_env_vars
            and not self.missing_packages
            and not self.changed_packages
            and not self.extra_packages
            and self.python_match
        )


def _get_live_python_version() -> str:
    try:
        result = subprocess.run(
            ["python", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception:
        return ""


def _get_live_pip_packages() -> Dict[str, str]:
    try:
        result = subprocess.run(
            ["pip", "list", "--format=freeze"], capture_output=True, text=True, timeout=10
        )
        packages: Dict[str, str] = {}
        for line in result.stdout.splitlines():
            if "==" in line:
                name, version = line.split("==", 1)
                packages[name.strip().lower()] = version.strip()
        return packages
    except Exception:
        return {}


def compare_with_live(
    snapshot: EnvSnapshot,
    exclude_env_keys: List[str] | None = None,
    check_extra_packages: bool = False,
) -> LiveComparison:
    """Compare *snapshot* against the currently running environment."""
    result = LiveComparison()

    # --- env vars ---
    live_env = capture_env_vars(exclude=exclude_env_keys)
    for key, snap_val in snapshot.env_vars.items():
        if key not in live_env:
            result.missing_env_vars.append(key)
        elif live_env[key] != snap_val:
            result.changed_env_vars[key] = (snap_val, live_env[key])
    if check_extra_packages:
        for key in live_env:
            if key not in snapshot.env_vars:
                result.extra_env_vars.append(key)

    # --- python version ---
    result.snapshot_python = snapshot.python_version
    result.live_python = _get_live_python_version()
    result.python_match = result.snapshot_python == result.live_python

    # --- pip packages ---
    live_pkgs = _get_live_pip_packages()
    for name, snap_ver in snapshot.pip_packages.items():
        norm = name.lower()
        if norm not in live_pkgs:
            result.missing_packages.append(name)
        elif live_pkgs[norm] != snap_ver:
            result.changed_packages[name] = (snap_ver, live_pkgs[norm])
    if check_extra_packages:
        snap_norm = {k.lower() for k in snapshot.pip_packages}
        for pkg in live_pkgs:
            if pkg not in snap_norm:
                result.extra_packages.append(pkg)

    return result
