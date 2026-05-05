"""Tests for envforge.differ module."""

import pytest
from envforge.snapshot import EnvSnapshot
from envforge.differ import (
    compare_snapshots,
    diff_env_vars,
    diff_pip_packages,
    format_diff,
    SnapshotDiff,
)


@pytest.fixture
def base_snapshot():
    return EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/home/user", "LANG": "en_US"},
        python_version="3.11.2",
        node_version="18.0.0",
        pip_packages=["requests==2.28.0", "flask==2.2.0", "numpy==1.24.0"],
    )


@pytest.fixture
def other_snapshot():
    return EnvSnapshot(
        env_vars={"PATH": "/usr/local/bin", "HOME": "/home/user", "EDITOR": "vim"},
        python_version="3.12.0",
        node_version="18.0.0",
        pip_packages=["requests==2.31.0", "flask==2.2.0", "pandas==2.0.0"],
    )


def test_diff_env_vars_added():
    base = {"A": "1", "B": "2"}
    other = {"A": "1", "B": "2", "C": "3"}
    added, removed, changed = diff_env_vars(base, other)
    assert "C" in added
    assert not removed
    assert not changed


def test_diff_env_vars_removed():
    base = {"A": "1", "B": "2"}
    other = {"A": "1"}
    added, removed, changed = diff_env_vars(base, other)
    assert "B" in removed
    assert not added
    assert not changed


def test_diff_env_vars_changed():
    base = {"A": "old"}
    other = {"A": "new"}
    added, removed, changed = diff_env_vars(base, other)
    assert "A" in changed
    assert changed["A"] == ("old", "new")


def test_diff_pip_packages_added():
    base = {"requests": "2.28.0"}
    other = {"requests": "2.28.0", "flask": "2.2.0"}
    added, removed, changed = diff_pip_packages(base, other)
    assert "flask==2.2.0" in added
    assert not removed


def test_diff_pip_packages_version_changed():
    base = {"requests": "2.28.0"}
    other = {"requests": "2.31.0"}
    added, removed, changed = diff_pip_packages(base, other)
    assert any(name == "requests" for name, _, _ in changed)


def test_compare_snapshots_detects_python_change(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    assert diff.python_version_changed == ("3.11.2", "3.12.0")


def test_compare_snapshots_no_node_change(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    assert diff.node_version_changed is None


def test_compare_snapshots_env_differences(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    assert "EDITOR" in diff.env_added
    assert "LANG" in diff.env_removed
    assert "PATH" in diff.env_changed


def test_compare_snapshots_pip_differences(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    assert any("pandas" in p for p in diff.pip_added)
    assert any("numpy" in p for p in diff.pip_removed)
    assert any(name == "requests" for name, _, _ in diff.pip_changed)


def test_has_differences_true(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    assert diff.has_differences()


def test_has_differences_false():
    snap = EnvSnapshot(env_vars={"A": "1"}, python_version="3.11", node_version=None, pip_packages=[])
    diff = compare_snapshots(snap, snap)
    assert not diff.has_differences()


def test_format_diff_no_differences():
    snap = EnvSnapshot(env_vars={}, python_version="3.11", node_version=None, pip_packages=[])
    diff = compare_snapshots(snap, snap)
    output = format_diff(diff)
    assert output == "No differences found."


def test_format_diff_contains_sections(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    output = format_diff(diff)
    assert "[python]" in output
    assert "[env" in output
    assert "[pip" in output
