"""Validate snapshots for completeness and consistency."""

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import EnvSnapshot

REQUIRED_ENV_KEYS = ["PATH", "HOME"]
MIN_PYTHON_VERSION_PARTS = 2  # e.g. "3.11" has at least 2 parts


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


def validate_env_vars(snapshot: EnvSnapshot, result: ValidationResult) -> None:
    """Check that required environment variables are present."""
    for key in REQUIRED_ENV_KEYS:
        if key not in snapshot.env_vars:
            result.errors.append(f"Missing required env var: {key}")


def validate_python_version(snapshot: EnvSnapshot, result: ValidationResult) -> None:
    """Validate python_version field format if present."""
    version = snapshot.python_version
    if not version:
        result.warnings.append("python_version is not set")
        return
    parts = version.split(".")
    if len(parts) < MIN_PYTHON_VERSION_PARTS:
        result.errors.append(
            f"python_version '{version}' does not look valid (expected e.g. '3.11.2')"
        )
    elif not all(p.isdigit() for p in parts):
        result.errors.append(
            f"python_version '{version}' contains non-numeric segments"
        )


def validate_pip_packages(snapshot: EnvSnapshot, result: ValidationResult) -> None:
    """Warn if pip packages list is empty."""
    if not snapshot.pip_packages:
        result.warnings.append("No pip packages recorded in snapshot")
        return
    for pkg in snapshot.pip_packages:
        if "==" not in pkg:
            result.warnings.append(
                f"Pip package entry '{pkg}' has no pinned version"
            )


def validate_snapshot(snapshot: EnvSnapshot) -> ValidationResult:
    """Run all validation checks and return a ValidationResult."""
    result = ValidationResult(valid=True)

    validate_env_vars(snapshot, result)
    validate_python_version(snapshot, result)
    validate_pip_packages(snapshot, result)

    if result.errors:
        result.valid = False

    return result
