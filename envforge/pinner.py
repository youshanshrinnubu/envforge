"""Pin and unpin specific packages or env vars in a snapshot for reproducibility locking."""

from dataclasses import dataclass, field
from typing import List, Optional
from envforge.snapshot import EnvSnapshot

PINNED_MARKER = "__pinned__"


@dataclass
class PinResult:
    pinned_packages: List[str] = field(default_factory=list)
    pinned_env_vars: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)


def pin_packages(snapshot: EnvSnapshot, package_names: List[str]) -> PinResult:
    """Mark specific pip packages as pinned (exact version locked)."""
    result = PinResult()
    pinned = dict(snapshot.pip_packages)

    for name in package_names:
        matched = [(k, v) for k, v in pinned.items() if k.lower() == name.lower()]
        if matched:
            key, version = matched[0]
            if not version.startswith(PINNED_MARKER):
                pinned[key] = f"{PINNED_MARKER}{version}"
            result.pinned_packages.append(key)
        else:
            result.skipped.append(name)

    snapshot.pip_packages = pinned
    return result


def unpin_packages(snapshot: EnvSnapshot, package_names: List[str]) -> PinResult:
    """Remove pin marker from specific pip packages."""
    result = PinResult()
    unpinned = dict(snapshot.pip_packages)

    for name in package_names:
        matched = [(k, v) for k, v in unpinned.items() if k.lower() == name.lower()]
        if matched:
            key, version = matched[0]
            if version.startswith(PINNED_MARKER):
                unpinned[key] = version[len(PINNED_MARKER):]
            result.pinned_packages.append(key)
        else:
            result.skipped.append(name)

    snapshot.pip_packages = unpinned
    return result


def pin_env_vars(snapshot: EnvSnapshot, var_names: List[str]) -> PinResult:
    """Mark specific environment variables as pinned."""
    result = PinResult()
    pinned_vars = set(getattr(snapshot, 'pinned_env_vars', []))

    for var in var_names:
        if var in snapshot.env_vars:
            pinned_vars.add(var)
            result.pinned_env_vars.append(var)
        else:
            result.skipped.append(var)

    snapshot.pinned_env_vars = list(pinned_vars)
    return result


def unpin_env_vars(snapshot: EnvSnapshot, var_names: List[str]) -> PinResult:
    """Remove pin marker from specific environment variables."""
    result = PinResult()
    pinned_vars = set(getattr(snapshot, 'pinned_env_vars', []))

    for var in var_names:
        if var in pinned_vars:
            pinned_vars.discard(var)
            result.pinned_env_vars.append(var)
        else:
            result.skipped.append(var)

    snapshot.pinned_env_vars = list(pinned_vars)
    return result


def list_pinned(snapshot: EnvSnapshot) -> dict:
    """Return a summary of all pinned packages and env vars."""
    pinned_pkgs = {
        k: v[len(PINNED_MARKER):]
        for k, v in snapshot.pip_packages.items()
        if v.startswith(PINNED_MARKER)
    }
    pinned_vars = list(getattr(snapshot, 'pinned_env_vars', []))
    return {"packages": pinned_pkgs, "env_vars": pinned_vars}
