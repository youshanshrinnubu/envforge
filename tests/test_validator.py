"""Tests for envforge.validator."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.validator import (
    ValidationResult,
    validate_env_vars,
    validate_pip_packages,
    validate_python_version,
    validate_snapshot,
)


@pytest.fixture
def valid_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/home/user"},
        python_version="3.11.2",
        node_version="18.0.0",
        pip_packages=["requests==2.31.0", "flask==3.0.0"],
    )


def test_valid_snapshot_passes(valid_snapshot):
    result = validate_snapshot(valid_snapshot)
    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_missing_required_env_var():
    snapshot = EnvSnapshot(
        env_vars={"HOME": "/home/user"},
        python_version="3.11.2",
        pip_packages=["requests==2.31.0"],
    )
    result = ValidationResult(valid=True)
    validate_env_vars(snapshot, result)
    assert any("PATH" in e for e in result.errors)


def test_missing_both_required_env_vars():
    snapshot = EnvSnapshot(env_vars={}, python_version="3.11.2", pip_packages=[])
    result = validate_snapshot(snapshot)
    assert result.valid is False
    assert len([e for e in result.errors if "PATH" in e or "HOME" in e]) == 2


def test_invalid_python_version_format():
    snapshot = EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/home/user"},
        python_version="3",
        pip_packages=["requests==2.31.0"],
    )
    result = ValidationResult(valid=True)
    validate_python_version(snapshot, result)
    assert any("python_version" in e for e in result.errors)


def test_non_numeric_python_version():
    snapshot = EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/home/user"},
        python_version="3.x.2",
        pip_packages=[],
    )
    result = ValidationResult(valid=True)
    validate_python_version(snapshot, result)
    assert any("non-numeric" in e for e in result.errors)


def test_missing_python_version_is_warning():
    snapshot = EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/home/user"},
        python_version=None,
        pip_packages=["requests==2.31.0"],
    )
    result = ValidationResult(valid=True)
    validate_python_version(snapshot, result)
    assert any("python_version" in w for w in result.warnings)
    assert result.errors == []


def test_empty_pip_packages_is_warning(valid_snapshot):
    valid_snapshot.pip_packages = []
    result = ValidationResult(valid=True)
    validate_pip_packages(valid_snapshot, result)
    assert any("pip packages" in w.lower() for w in result.warnings)


def test_unpinned_pip_package_is_warning():
    snapshot = EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/home/user"},
        python_version="3.11.2",
        pip_packages=["requests"],
    )
    result = ValidationResult(valid=True)
    validate_pip_packages(snapshot, result)
    assert any("pinned" in w for w in result.warnings)


def test_validation_result_bool_false_on_errors():
    result = ValidationResult(valid=False, errors=["something wrong"])
    assert not result


def test_validation_result_bool_true_when_valid():
    result = ValidationResult(valid=True)
    assert result
