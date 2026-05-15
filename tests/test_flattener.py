"""Tests for envforge.flattener."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.flattener import (
    FlattenResult,
    flatten_env_vars,
    flatten_pip_packages,
    flatten_snapshot,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={
            "AWS__REGION": "us-east-1",
            "AWS__SECRET": "abc123",
            "HOME": "/home/user",
            "PATH": "/usr/bin",
        },
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages=[
            {"name": "requests[security]", "version": "2.31.0"},
            {"name": "boto3", "version": "1.26.0"},
            {"name": "django[argon2]", "version": "4.2.0"},
        ],
        label="test",
    )


@pytest.fixture
def empty_snapshot():
    return EnvSnapshot(
        env_vars={},
        python_version=None,
        node_version=None,
        pip_packages=[],
        label=None,
    )


def test_flatten_result_bool_true_when_flattened(sample_snapshot):
    result = flatten_env_vars(sample_snapshot)
    assert bool(result) is True


def test_flatten_result_bool_false_when_nothing_flattened(empty_snapshot):
    result = flatten_env_vars(empty_snapshot)
    assert bool(result) is False


def test_flatten_env_vars_replaces_double_underscore(sample_snapshot):
    result = flatten_env_vars(sample_snapshot)
    assert "AWS_REGION" in result.snapshot.env_vars
    assert "AWS_SECRET" in result.snapshot.env_vars


def test_flatten_env_vars_removes_original_keys(sample_snapshot):
    result = flatten_env_vars(sample_snapshot)
    assert "AWS__REGION" not in result.snapshot.env_vars
    assert "AWS__SECRET" not in result.snapshot.env_vars


def test_flatten_env_vars_preserves_non_separator_keys(sample_snapshot):
    result = flatten_env_vars(sample_snapshot)
    assert result.snapshot.env_vars["HOME"] == "/home/user"
    assert result.snapshot.env_vars["PATH"] == "/usr/bin"


def test_flatten_env_vars_records_flattened_keys(sample_snapshot):
    result = flatten_env_vars(sample_snapshot)
    assert "AWS__REGION" in result.flattened_env_keys
    assert "AWS__SECRET" in result.flattened_env_keys


def test_flatten_env_vars_lowercase(sample_snapshot):
    result = flatten_env_vars(sample_snapshot, lowercase_keys=True)
    assert "aws_region" in result.snapshot.env_vars
    assert "aws_secret" in result.snapshot.env_vars


def test_flatten_env_vars_collision_emits_warning():
    snap = EnvSnapshot(
        env_vars={"A__B": "first", "A_B": "second"},
        python_version=None, node_version=None, pip_packages=[], label=None,
    )
    result = flatten_env_vars(snap)
    assert any("Collision" in w for w in result.warnings)


def test_flatten_pip_packages_strips_extras(sample_snapshot):
    result = flatten_pip_packages(sample_snapshot)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "requests" in names
    assert "django" in names
    assert "requests[security]" not in names


def test_flatten_pip_packages_records_flattened(sample_snapshot):
    result = flatten_pip_packages(sample_snapshot)
    assert "requests[security]" in result.flattened_pkg_names
    assert "django[argon2]" in result.flattened_pkg_names


def test_flatten_pip_packages_preserves_plain_packages(sample_snapshot):
    result = flatten_pip_packages(sample_snapshot)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "boto3" in names


def test_flatten_snapshot_combines_both(sample_snapshot):
    result = flatten_snapshot(sample_snapshot)
    assert "AWS_REGION" in result.snapshot.env_vars
    pkg_names = [p["name"] for p in result.snapshot.pip_packages]
    assert "requests" in pkg_names
    assert bool(result) is True


def test_flatten_snapshot_preserves_metadata(sample_snapshot):
    result = flatten_snapshot(sample_snapshot)
    assert result.snapshot.python_version == "3.11.0"
    assert result.snapshot.label == "test"


def test_flatten_empty_snapshot_no_error(empty_snapshot):
    result = flatten_snapshot(empty_snapshot)
    assert result.snapshot.env_vars == {}
    assert result.snapshot.pip_packages == []
    assert bool(result) is False
