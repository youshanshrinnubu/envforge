"""Tests for envforge.stripper."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.stripper import (
    StripResult,
    strip_env_vars,
    strip_pip_packages,
    strip_snapshot,
    strip_versions,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        label="test-snap",
        python_version="3.11.2",
        node_version="18.0.0",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin", "SECRET": "abc"},
        pip_packages=[
            {"name": "requests", "version": "2.31.0"},
            {"name": "flask", "version": "3.0.0"},
        ],
        conda_packages=[],
    )


def test_strip_result_bool_true_when_stripped(sample_snapshot):
    result = strip_env_vars(sample_snapshot)
    assert bool(result) is True


def test_strip_result_bool_false_when_nothing_stripped():
    snap = EnvSnapshot(
        label="empty",
        python_version=None,
        node_version=None,
        env_vars={},
        pip_packages=[],
        conda_packages=[],
    )
    result = strip_env_vars(snap)
    assert bool(result) is False


def test_strip_env_vars_clears_env_vars(sample_snapshot):
    result = strip_env_vars(sample_snapshot)
    assert result.snapshot.env_vars == {}


def test_strip_env_vars_preserves_packages(sample_snapshot):
    result = strip_env_vars(sample_snapshot)
    assert len(result.snapshot.pip_packages) == 2


def test_strip_env_vars_records_original_count(sample_snapshot):
    result = strip_env_vars(sample_snapshot)
    assert result.original_env_var_count == 3


def test_strip_pip_packages_clears_packages(sample_snapshot):
    result = strip_pip_packages(sample_snapshot)
    assert result.snapshot.pip_packages == []


def test_strip_pip_packages_preserves_env_vars(sample_snapshot):
    result = strip_pip_packages(sample_snapshot)
    assert len(result.snapshot.env_vars) == 3


def test_strip_pip_packages_records_original_count(sample_snapshot):
    result = strip_pip_packages(sample_snapshot)
    assert result.original_package_count == 2


def test_strip_versions_removes_python_and_node(sample_snapshot):
    result = strip_versions(sample_snapshot)
    assert result.snapshot.python_version is None
    assert result.snapshot.node_version is None


def test_strip_versions_stripped_fields(sample_snapshot):
    result = strip_versions(sample_snapshot)
    assert "python_version" in result.stripped_fields
    assert "node_version" in result.stripped_fields


def test_strip_versions_does_not_alter_env_vars(sample_snapshot):
    result = strip_versions(sample_snapshot)
    assert result.snapshot.env_vars == sample_snapshot.env_vars


def test_strip_snapshot_all_flags(sample_snapshot):
    result = strip_snapshot(sample_snapshot, env_vars=True, pip_packages=True, versions=True)
    assert result.snapshot.env_vars == {}
    assert result.snapshot.pip_packages == []
    assert result.snapshot.python_version is None
    assert result.snapshot.node_version is None


def test_strip_snapshot_keep_only_keys(sample_snapshot):
    result = strip_snapshot(sample_snapshot, keep_only_keys=["HOME"])
    assert list(result.snapshot.env_vars.keys()) == ["HOME"]
    assert "env_vars(filtered)" in result.stripped_fields


def test_strip_snapshot_keep_only_keys_ignored_with_env_vars_flag(sample_snapshot):
    result = strip_snapshot(sample_snapshot, env_vars=True, keep_only_keys=["HOME"])
    assert result.snapshot.env_vars == {}


def test_strip_snapshot_does_not_mutate_original(sample_snapshot):
    strip_snapshot(sample_snapshot, env_vars=True, pip_packages=True, versions=True)
    assert sample_snapshot.env_vars == {"HOME": "/home/user", "PATH": "/usr/bin", "SECRET": "abc"}
    assert len(sample_snapshot.pip_packages) == 2
    assert sample_snapshot.python_version == "3.11.2"
