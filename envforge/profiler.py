"""Profile snapshots to summarize key environment characteristics."""

from dataclasses import dataclass, field
from typing import List, Optional
from envforge.snapshot import EnvSnapshot


@dataclass
class SnapshotProfile:
    """Summary profile derived from an EnvSnapshot."""
    python_version: Optional[str]
    node_version: Optional[str]
    pip_package_count: int
    env_var_count: int
    top_packages: List[str] = field(default_factory=list)
    has_virtual_env: bool = False
    has_conda_env: bool = False
    shell: Optional[str] = None
    notes: List[str] = field(default_factory=list)


def _top_packages(packages: dict, n: int = 5) -> List[str]:
    """Return up to n package names sorted alphabetically."""
    return sorted(packages.keys())[:n]


def _detect_virtual_env(env_vars: dict) -> bool:
    """Return True if a virtual environment is active."""
    return "VIRTUAL_ENV" in env_vars or "CONDA_DEFAULT_ENV" in env_vars


def _detect_conda_env(env_vars: dict) -> bool:
    """Return True if a Conda environment is active."""
    return "CONDA_DEFAULT_ENV" in env_vars or "CONDA_PREFIX" in env_vars


def _detect_shell(env_vars: dict) -> Optional[str]:
    """Return the shell name from env vars if available."""
    shell_path = env_vars.get("SHELL", "")
    if shell_path:
        return shell_path.split("/")[-1]
    return None


def _build_notes(snapshot: EnvSnapshot) -> List[str]:
    """Generate human-readable notes about the snapshot."""
    notes = []
    if not snapshot.python_version:
        notes.append("Python version not recorded.")
    if not snapshot.node_version:
        notes.append("Node.js version not recorded.")
    if not snapshot.pip_packages:
        notes.append("No pip packages captured.")
    if len(snapshot.env_vars) == 0:
        notes.append("No environment variables captured.")
    return notes


def profile_snapshot(snapshot: EnvSnapshot) -> SnapshotProfile:
    """Derive a SnapshotProfile from the given EnvSnapshot."""
    return SnapshotProfile(
        python_version=snapshot.python_version,
        node_version=snapshot.node_version,
        pip_package_count=len(snapshot.pip_packages),
        env_var_count=len(snapshot.env_vars),
        top_packages=_top_packages(snapshot.pip_packages),
        has_virtual_env=_detect_virtual_env(snapshot.env_vars),
        has_conda_env=_detect_conda_env(snapshot.env_vars),
        shell=_detect_shell(snapshot.env_vars),
        notes=_build_notes(snapshot),
    )


def format_profile(profile: SnapshotProfile) -> str:
    """Return a human-readable string summary of the profile."""
    lines = [
        f"Python : {profile.python_version or 'unknown'}",
        f"Node   : {profile.node_version or 'unknown'}",
        f"Shell  : {profile.shell or 'unknown'}",
        f"Pip packages : {profile.pip_package_count}",
        f"Env vars     : {profile.env_var_count}",
        f"VirtualEnv   : {'yes' if profile.has_virtual_env else 'no'}",
        f"Conda env    : {'yes' if profile.has_conda_env else 'no'}",
    ]
    if profile.top_packages:
        lines.append("Top packages : " + ", ".join(profile.top_packages))
    if profile.notes:
        lines.append("Notes:")
        for note in profile.notes:
            lines.append(f"  - {note}")
    return "\n".join(lines)
