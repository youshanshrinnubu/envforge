"""Clone and duplicate snapshots with optional field overrides."""

from __future__ import annotations

import copy
import dataclasses
from typing import Optional

from envforge.snapshot import EnvSnapshot


@dataclasses.dataclass
class CloneResult:
    original_label: str
    cloned_label: str
    success: bool
    message: str = ""

    def __bool__(self) -> bool:
        return self.success


def clone_snapshot(
    snapshot: EnvSnapshot,
    new_label: str,
    override_env_vars: Optional[dict] = None,
    override_pip_packages: Optional[dict] = None,
    override_python_version: Optional[str] = None,
    override_node_version: Optional[str] = None,
) -> tuple[EnvSnapshot, CloneResult]:
    """Create a deep copy of a snapshot with optional field overrides.

    Returns the new snapshot and a CloneResult describing the operation.
    """
    if not new_label or not new_label.strip():
        dummy = copy.deepcopy(snapshot)
        result = CloneResult(
            original_label=snapshot.label,
            cloned_label="",
            success=False,
            message="new_label must be a non-empty string",
        )
        return dummy, result

    cloned = copy.deepcopy(snapshot)
    cloned.label = new_label.strip()

    if override_env_vars is not None:
        cloned.env_vars = dict(override_env_vars)

    if override_pip_packages is not None:
        cloned.pip_packages = dict(override_pip_packages)

    if override_python_version is not None:
        cloned.python_version = override_python_version

    if override_node_version is not None:
        cloned.node_version = override_node_version

    result = CloneResult(
        original_label=snapshot.label,
        cloned_label=cloned.label,
        success=True,
        message=f"Cloned '{snapshot.label}' -> '{cloned.label}'",
    )
    return cloned, result


def clone_with_env_patch(snapshot: EnvSnapshot, new_label: str, patch: dict) -> tuple[EnvSnapshot, CloneResult]:
    """Clone a snapshot and merge patch keys into its env_vars."""
    merged_env = {**snapshot.env_vars, **patch}
    return clone_snapshot(snapshot, new_label, override_env_vars=merged_env)
