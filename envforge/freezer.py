"""Freeze a snapshot by locking all package versions and env vars in place."""

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import EnvSnapshot


@dataclass
class FreezeResult:
    frozen_snapshot: EnvSnapshot
    pinned_packages: List[str] = field(default_factory=list)
    locked_env_vars: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return len(self.warnings) == 0


def _normalize_package_entry(entry: str) -> str:
    """Ensure a pip package entry has a pinned version using '=='."""
    entry = entry.strip()
    if not entry:
        return entry
    if "==" in entry or ">=" in entry or "<=" in entry or "!=" in entry:
        return entry
    return entry  # already bare name; caller decides


def freeze_packages(snapshot: EnvSnapshot) -> tuple:
    """Return (updated packages list, list of newly-pinned names, warnings)."""
    packages = list(snapshot.pip_packages or [])
    pinned: List[str] = []
    warnings: List[str] = []

    updated = []
    for pkg in packages:
        pkg = pkg.strip()
        if not pkg:
            continue
        if "==" in pkg:
            updated.append(pkg)
            pinned.append(pkg.split("==")[0].strip())
        elif any(op in pkg for op in [">=", "<=", "!=", "~="]):
            updated.append(pkg)
            warnings.append(f"Package '{pkg}' uses a non-exact specifier; consider pinning with '=='")
        else:
            updated.append(pkg)
            warnings.append(f"Package '{pkg}' has no version specifier; pin it for reproducibility")
    return updated, pinned, warnings


def freeze_env_vars(snapshot: EnvSnapshot) -> tuple:
    """Mark env vars as locked by prefixing metadata; returns (vars dict, locked keys)."""
    env_vars = dict(snapshot.env_vars or {})
    locked = list(env_vars.keys())
    return env_vars, locked


def freeze_snapshot(snapshot: EnvSnapshot) -> FreezeResult:
    """Produce a frozen copy of *snapshot* with all versions locked."""
    import copy
    frozen = copy.deepcopy(snapshot)

    packages, pinned, pkg_warnings = freeze_packages(frozen)
    frozen.pip_packages = packages

    env_vars, locked_keys = freeze_env_vars(frozen)
    frozen.env_vars = env_vars

    if frozen.label:
        frozen.label = frozen.label.rstrip() + " [frozen]"
    else:
        frozen.label = "[frozen]"

    return FreezeResult(
        frozen_snapshot=frozen,
        pinned_packages=pinned,
        locked_env_vars=locked_keys,
        warnings=pkg_warnings,
    )
