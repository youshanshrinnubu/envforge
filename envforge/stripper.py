"""Strip fields or sections from a snapshot to produce a minimal or sanitized version."""

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class StripResult:
    snapshot: EnvSnapshot
    stripped_fields: List[str] = field(default_factory=list)
    original_env_var_count: int = 0
    original_package_count: int = 0

    def __bool__(self) -> bool:
        return len(self.stripped_fields) > 0


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        label=snap.label,
        python_version=snap.python_version,
        node_version=snap.node_version,
        env_vars=dict(snap.env_vars),
        pip_packages=list(snap.pip_packages),
        conda_packages=list(snap.conda_packages),
    )


def strip_env_vars(snap: EnvSnapshot) -> StripResult:
    """Remove all environment variables from a snapshot."""
    result = _copy_snapshot(snap)
    count = len(result.env_vars)
    result.env_vars.clear()
    stripped = ["env_vars"] if count > 0 else []
    return StripResult(
        snapshot=result,
        stripped_fields=stripped,
        original_env_var_count=count,
        original_package_count=len(snap.pip_packages),
    )


def strip_pip_packages(snap: EnvSnapshot) -> StripResult:
    """Remove all pip packages from a snapshot."""
    result = _copy_snapshot(snap)
    count = len(result.pip_packages)
    result.pip_packages.clear()
    stripped = ["pip_packages"] if count > 0 else []
    return StripResult(
        snapshot=result,
        stripped_fields=stripped,
        original_env_var_count=len(snap.env_vars),
        original_package_count=count,
    )


def strip_versions(snap: EnvSnapshot) -> StripResult:
    """Remove python_version and node_version from a snapshot."""
    result = _copy_snapshot(snap)
    stripped = []
    if result.python_version:
        result.python_version = None
        stripped.append("python_version")
    if result.node_version:
        result.node_version = None
        stripped.append("node_version")
    return StripResult(
        snapshot=result,
        stripped_fields=stripped,
        original_env_var_count=len(snap.env_vars),
        original_package_count=len(snap.pip_packages),
    )


def strip_snapshot(
    snap: EnvSnapshot,
    env_vars: bool = False,
    pip_packages: bool = False,
    versions: bool = False,
    keep_only_keys: Optional[List[str]] = None,
) -> StripResult:
    """Composite strip operation. Optionally keep only specific env var keys."""
    result = _copy_snapshot(snap)
    stripped: List[str] = []
    orig_env = len(snap.env_vars)
    orig_pkg = len(snap.pip_packages)

    if env_vars:
        result.env_vars.clear()
        if orig_env > 0:
            stripped.append("env_vars")

    if keep_only_keys is not None and not env_vars:
        removed = {k: v for k, v in result.env_vars.items() if k not in keep_only_keys}
        for k in removed:
            del result.env_vars[k]
        if removed:
            stripped.append("env_vars(filtered)")

    if pip_packages:
        result.pip_packages.clear()
        if orig_pkg > 0:
            stripped.append("pip_packages")

    if versions:
        if result.python_version:
            result.python_version = None
            stripped.append("python_version")
        if result.node_version:
            result.node_version = None
            stripped.append("node_version")

    return StripResult(
        snapshot=result,
        stripped_fields=stripped,
        original_env_var_count=orig_env,
        original_package_count=orig_pkg,
    )
