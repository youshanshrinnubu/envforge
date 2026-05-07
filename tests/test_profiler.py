"""Tests for envforge.profiler."""

import pytest
from envforge.snapshot import EnvSnapshot
from envforge.profiler import (
    SnapshotProfile,
    profile_snapshot,
    format_profile,
    _top_packages,
    _detect_virtual_env,
    _detect_conda_env,
    _detect_shell,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        python_version="3.11.2",
        node_version="18.0.0",
        pip_packages={"requests": "2.28.0", "flask": "2.3.0", "numpy": "1.24.0"},
        env_vars={
            "HOME": "/home/user",
            "SHELL": "/bin/zsh",
            "VIRTUAL_ENV": "/home/user/.venv",
        },
    )


@pytest.fixture
def empty_snapshot():
    return EnvSnapshot(
        python_version=None,
        node_version=None,
        pip_packages={},
        env_vars={},
    )


def test_profile_snapshot_returns_profile(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert isinstance(profile, SnapshotProfile)


def test_profile_python_version(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.python_version == "3.11.2"


def test_profile_node_version(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.node_version == "18.0.0"


def test_profile_pip_package_count(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.pip_package_count == 3


def test_profile_env_var_count(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.env_var_count == 3


def test_profile_top_packages_sorted(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.top_packages == sorted(["requests", "flask", "numpy"])


def test_profile_detects_virtual_env(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.has_virtual_env is True


def test_profile_no_virtual_env():
    snap = EnvSnapshot(python_version="3.10", node_version=None,
                       pip_packages={}, env_vars={"HOME": "/home/user"})
    profile = profile_snapshot(snap)
    assert profile.has_virtual_env is False


def test_profile_detects_conda_env():
    snap = EnvSnapshot(python_version="3.10", node_version=None,
                       pip_packages={}, env_vars={"CONDA_DEFAULT_ENV": "myenv"})
    profile = profile_snapshot(snap)
    assert profile.has_conda_env is True


def test_profile_shell_detected(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    assert profile.shell == "zsh"


def test_profile_shell_none_when_missing():
    snap = EnvSnapshot(python_version="3.10", node_version=None,
                       pip_packages={}, env_vars={})
    profile = profile_snapshot(snap)
    assert profile.shell is None


def test_profile_notes_for_empty_snapshot(empty_snapshot):
    profile = profile_snapshot(empty_snapshot)
    assert any("Python" in n for n in profile.notes)
    assert any("pip" in n.lower() for n in profile.notes)


def test_format_profile_contains_python(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    output = format_profile(profile)
    assert "3.11.2" in output


def test_format_profile_contains_shell(sample_snapshot):
    profile = profile_snapshot(sample_snapshot)
    output = format_profile(profile)
    assert "zsh" in output


def test_top_packages_limit():
    pkgs = {f"pkg{i}": "1.0" for i in range(10)}
    result = _top_packages(pkgs, n=3)
    assert len(result) == 3


def test_detect_virtual_env_false_without_key():
    assert _detect_virtual_env({"HOME": "/home/user"}) is False


def test_detect_conda_env_via_prefix():
    assert _detect_conda_env({"CONDA_PREFIX": "/opt/conda/envs/base"}) is True
