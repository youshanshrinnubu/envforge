"""Flatten nested or prefixed env vars and package groups into a single-level snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class FlattenResult:
    snapshot: EnvSnapshot
    flattened_env_keys: List[str] = field(default_factory=list)
    flattened_pkg_names: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.flattened_env_keys or self.flattened_pkg_names)


def _copy_snapshot(snapshot: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        env_vars=dict(snapshot.env_vars),
        python_version=snapshot.python_version,
        node_version=snapshot.node_version,
        pip_packages=list(snapshot.pip_packages),
        label=snapshot.label,
    )


def flatten_env_vars(
    snapshot: EnvSnapshot,
    separator: str = "__",
    lowercase_keys: bool = False,
) -> FlattenResult:
    """Collapse keys that contain *separator* by replacing it with a single underscore.

    E.g. ``AWS__REGION`` -> ``AWS_REGION`` when separator is ``__``.
    Duplicate targets are kept from the last key encountered and a warning is emitted.
    """
    copy = _copy_snapshot(snapshot)
    flattened: List[str] = []
    warnings: List[str] = []
    new_env: Dict[str, str] = {}

    for key, value in snapshot.env_vars.items():
        if separator in key:
            new_key = key.replace(separator, "_")
            if lowercase_keys:
                new_key = new_key.lower()
            if new_key in new_env:
                warnings.append(
                    f"Collision: '{key}' -> '{new_key}' already exists; overwriting."
                )
            new_env[new_key] = value
            flattened.append(key)
        else:
            target = key.lower() if lowercase_keys else key
            new_env[target] = value

    copy.env_vars = new_env
    return FlattenResult(snapshot=copy, flattened_env_keys=flattened, warnings=warnings)


def flatten_pip_packages(snapshot: EnvSnapshot) -> FlattenResult:
    """Normalise package list by stripping extras markers (e.g. ``requests[security]`` -> ``requests``).

    Duplicate normalised names are deduplicated, keeping the last entry.
    """
    copy = _copy_snapshot(snapshot)
    flattened: List[str] = []
    warnings: List[str] = []
    seen: Dict[str, dict] = {}

    for pkg in snapshot.pip_packages:
        name = pkg.get("name", "")
        base_name = name.split("[")[0].strip() if "[" in name else name
        if base_name != name:
            if base_name in seen:
                warnings.append(
                    f"Collision: '{name}' normalises to '{base_name}' which already exists; overwriting."
                )
            flattened.append(name)
            seen[base_name] = dict(pkg, name=base_name)
        else:
            seen[base_name] = pkg

    copy.pip_packages = list(seen.values())
    return FlattenResult(snapshot=copy, flattened_pkg_names=flattened, warnings=warnings)


def flatten_snapshot(
    snapshot: EnvSnapshot,
    separator: str = "__",
    lowercase_keys: bool = False,
) -> FlattenResult:
    """Run both env-var and package flattening and merge results."""
    env_result = flatten_env_vars(snapshot, separator=separator, lowercase_keys=lowercase_keys)
    pkg_result = flatten_pip_packages(env_result.snapshot)
    return FlattenResult(
        snapshot=pkg_result.snapshot,
        flattened_env_keys=env_result.flattened_env_keys,
        flattened_pkg_names=pkg_result.flattened_pkg_names,
        warnings=env_result.warnings + pkg_result.warnings,
    )
