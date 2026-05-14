"""Tests for envforge.freezer."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.freezer import (
    FreezeResult,
    freeze_packages,
    freeze_env_vars,
    freeze_snapshot,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        label="my-env",
        python_version="3.11.2",
        node_version="18.0.0",
        pip_packages=["requests==2.31.0", "flask>=2.0", "numpy", "black==23.1.0"],
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin", "DEBUG": "1"},
    )


@pytest.fixture
def empty_snapshot():
    return EnvSnapshot(
        label=None,
        python_version=None,
        node_version=None,
        pip_packages=[],
        env_vars={},
    )


# --- FreezeResult ---

def test_freeze_result_bool_true_when_no_warnings():
    snap = EnvSnapshot(label="x", python_version=None, node_version=None,
                       pip_packages=[], env_vars={})
    result = FreezeResult(frozen_snapshot=snap, warnings=[])
    assert bool(result) is True


def test_freeze_result_bool_false_when_warnings():
    snap = EnvSnapshot(label="x", python_version=None, node_version=None,
                       pip_packages=[], env_vars={})
    result = FreezeResult(frozen_snapshot=snap, warnings=["some warning"])
    assert bool(result) is False


# --- freeze_packages ---

def test_freeze_packages_keeps_pinned(sample_snapshot):
    _, pinned, _ = freeze_packages(sample_snapshot)
    assert "requests" in pinned
    assert "black" in pinned


def test_freeze_packages_warns_on_range_specifier(sample_snapshot):
    _, _, warnings = freeze_packages(sample_snapshot)
    assert any("flask" in w for w in warnings)


def test_freeze_packages_warns_on_bare_name(sample_snapshot):
    _, _, warnings = freeze_packages(sample_snapshot)
    assert any("numpy" in w for w in warnings)


def test_freeze_packages_empty_list(empty_snapshot):
    packages, pinned, warnings = freeze_packages(empty_snapshot)
    assert packages == []
    assert pinned == []
    assert warnings == []


# --- freeze_env_vars ---

def test_freeze_env_vars_returns_all_keys(sample_snapshot):
    env_vars, locked = freeze_env_vars(sample_snapshot)
    assert set(locked) == {"HOME", "PATH", "DEBUG"}


def test_freeze_env_vars_empty(empty_snapshot):
    env_vars, locked = freeze_env_vars(empty_snapshot)
    assert locked == []
    assert env_vars == {}


# --- freeze_snapshot ---

def test_freeze_snapshot_returns_freeze_result(sample_snapshot):
    result = freeze_snapshot(sample_snapshot)
    assert isinstance(result, FreezeResult)


def test_freeze_snapshot_does_not_mutate_original(sample_snapshot):
    original_label = sample_snapshot.label
    freeze_snapshot(sample_snapshot)
    assert sample_snapshot.label == original_label


def test_freeze_snapshot_appends_frozen_label(sample_snapshot):
    result = freeze_snapshot(sample_snapshot)
    assert "[frozen]" in result.frozen_snapshot.label


def test_freeze_snapshot_label_none_becomes_frozen(empty_snapshot):
    result = freeze_snapshot(empty_snapshot)
    assert result.frozen_snapshot.label == "[frozen]"


def test_freeze_snapshot_locked_env_vars_count(sample_snapshot):
    result = freeze_snapshot(sample_snapshot)
    assert len(result.locked_env_vars) == len(sample_snapshot.env_vars)


def test_freeze_snapshot_preserves_python_version(sample_snapshot):
    result = freeze_snapshot(sample_snapshot)
    assert result.frozen_snapshot.python_version == sample_snapshot.python_version


def test_freeze_snapshot_has_warnings_for_unpinned(sample_snapshot):
    result = freeze_snapshot(sample_snapshot)
    assert len(result.warnings) > 0
