"""Core module for capturing a snapshot of the current shell environment."""

import os
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnvSnapshot:
    """Represents a captured snapshot of a dev environment."""

    shell: str
    env_vars: dict[str, str] = field(default_factory=dict)
    installed_packages: list[str] = field(default_factory=list)
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    working_directory: str = ""


def capture_env_vars(exclude_keys: list[str] | None = None) -> dict[str, str]:
    """Capture current environment variables, optionally excluding certain keys."""
    exclude = set(exclude_keys or ["LS_COLORS", "PS1", "PS2"])
    return {k: v for k, v in os.environ.items() if k not in exclude}


def capture_python_version() -> Optional[str]:
    """Return the current Python version string, or None if unavailable."""
    if shutil.which("python3"):
        result = subprocess.run(
            ["python3", "--version"], capture_output=True, text=True
        )
        return result.stdout.strip() or result.stderr.strip()
    return None


def capture_node_version() -> Optional[str]:
    """Return the current Node.js version string, or None if unavailable."""
    if shutil.which("node"):
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True
        )
        return result.stdout.strip()
    return None


def capture_pip_packages() -> list[str]:
    """Return a list of installed pip packages in 'name==version' format."""
    if not shutil.which("pip3") and not shutil.which("pip"):
        return []
    cmd = "pip3" if shutil.which("pip3") else "pip"
    result = subprocess.run(
        [cmd, "freeze"], capture_output=True, text=True
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _run_command(cmd: list[str]) -> Optional[str]:
    """Run a subprocess command and return stripped stdout, or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def take_snapshot() -> EnvSnapshot:
    """Capture a full snapshot of the current shell environment."""
    return EnvSnapshot(
        shell=os.environ.get("SHELL", "unknown"),
        env_vars=capture_env_vars(),
        installed_packages=capture_pip_packages(),
        python_version=capture_python_version(),
        node_version=capture_node_version(),
        working_directory=os.getcwd(),
    )
