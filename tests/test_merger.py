"""Tests for envforge.merger module."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.merger import (
    MergeResult,
    merge_env_vars,
    merge_pip_packages,
    merge_snapshots,
)


@pytest.fixture
def base_snapshot():
    return EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/root", "EDITOR": "vim"},
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages={"requests": "2.28.0", "flask": "2.2.0"},
        label="base",
    )


@pytest.fixture
def other_snapshot():
    return EnvSnapshot(
        env_vars={"PATH": "/usr/local/bin", "HOME": "/root", "DEBUG": "1"},
        python_version="3.12.0",
        node_version=None,
        pip_packages={"requests": "2.31.0", "numpy": "1.25.0"},
        label="other",
    )


def test_merge_env_vars_prefer_other():
    base = {"A": "1", "B": "2"}
    other = {"A": "99", "C": "3"}
    merged, conflicts = merge_env_vars(base, other, strategy="prefer_other")
    assert merged["A"] == "99"
    assert merged["B"] == "2"
    assert merged["C"] == "3"
    assert "A" in conflicts
    assert conflicts["A"] == ("1", "99")


def test_merge_env_vars_prefer_base():
    base = {"A": "1", "B": "2"}
    other = {"A": "99", "C": "3"}
    merged, conflicts = merge_env_vars(base, other, strategy="prefer_base")
    assert merged["A"] == "1"  # base wins
    assert merged["C"] == "3"  # new key still added
    assert "A" in conflicts


def test_merge_env_vars_no_conflicts():
    base = {"A": "1"}
    other = {"B": "2"}
    merged, conflicts = merge_env_vars(base, other)
    assert merged == {"A": "1", "B": "2"}
    assert conflicts == {}


def test_merge_pip_packages_prefer_other():
    base = {"requests": "2.28.0", "flask": "2.2.0"}
    other = {"requests": "2.31.0", "numpy": "1.25.0"}
    merged, conflicts = merge_pip_packages(base, other, strategy="prefer_other")
    assert merged["requests"] == "2.31.0"
    assert merged["flask"] == "2.2.0"
    assert merged["numpy"] == "1.25.0"
    assert "requests" in conflicts


def test_merge_pip_packages_prefer_base():
    base = {"requests": "2.28.0"}
    other = {"requests": "2.31.0"}
    merged, conflicts = merge_pip_packages(base, other, strategy="prefer_base")
    assert merged["requests"] == "2.28.0"
    assert conflicts["requests"] == ("2.28.0", "2.31.0")


def test_merge_snapshots_returns_merge_result(base_snapshot, other_snapshot):
    result = merge_snapshots(base_snapshot, other_snapshot)
    assert isinstance(result, MergeResult)
    assert isinstance(result.snapshot, EnvSnapshot)


def test_merge_snapshots_prefer_other_python_version(base_snapshot, other_snapshot):
    result = merge_snapshots(base_snapshot, other_snapshot, strategy="prefer_other")
    assert result.snapshot.python_version == "3.12.0"


def test_merge_snapshots_conflicts_recorded(base_snapshot, other_snapshot):
    result = merge_snapshots(base_snapshot, other_snapshot)
    assert "env:PATH" in result.conflicts
    assert "pip:requests" in result.conflicts


def test_merge_snapshots_notes_populated(base_snapshot, other_snapshot):
    result = merge_snapshots(base_snapshot, other_snapshot)
    assert len(result.notes) > 0
    assert any("env var" in note for note in result.notes)


def test_merge_snapshots_custom_label(base_snapshot, other_snapshot):
    result = merge_snapshots(base_snapshot, other_snapshot, label="my-merged-env")
    assert result.snapshot.label == "my-merged-env"


def test_merge_snapshots_default_label(base_snapshot, other_snapshot):
    result = merge_snapshots(base_snapshot, other_snapshot)
    assert "base" in result.snapshot.label
    assert "other" in result.snapshot.label
