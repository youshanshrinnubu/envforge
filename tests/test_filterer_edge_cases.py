"""Edge-case tests for envforge.filterer."""
from __future__ import annotations

import pytest

from envforge.filterer import filter_env_vars, filter_pip_packages, filter_snapshot
from envforge.snapshot import EnvSnapshot


@pytest.fixture()
def empty_snapshot() -> EnvSnapshot:
    snap = EnvSnapshot()
    snap.env_vars = {}
    snap.pip_packages = []
    snap.python_version = ""
    return snap


def test_filter_env_vars_empty_snapshot(empty_snapshot):
    result = filter_env_vars(empty_snapshot, lambda k, v: True)
    assert result.filtered_env_count == 0
    assert bool(result) is False


def test_filter_pip_packages_empty_snapshot(empty_snapshot):
    result = filter_pip_packages(empty_snapshot, lambda p: True)
    assert result.filtered_pkg_count == 0
    assert bool(result) is False


def test_filter_env_vars_remove_all(empty_snapshot):
    empty_snapshot.env_vars = {"A": "1", "B": "2"}
    result = filter_env_vars(empty_snapshot, lambda k, v: False)
    assert result.snapshot.env_vars == {}
    assert result.filtered_env_count == 0


def test_filter_pip_packages_remove_all():
    snap = EnvSnapshot()
    snap.env_vars = {}
    snap.pip_packages = [{"name": "x", "version": "1.0"}]
    snap.python_version = ""
    result = filter_pip_packages(snap, lambda p: False)
    assert result.snapshot.pip_packages == []


def test_filter_snapshot_preserves_python_version():
    snap = EnvSnapshot()
    snap.env_vars = {"KEY": "val"}
    snap.pip_packages = []
    snap.python_version = "3.10.0"
    result = filter_snapshot(snap, env_predicate=lambda k, v: False)
    assert result.snapshot.python_version == "3.10.0"


def test_filter_snapshot_preserves_node_version():
    snap = EnvSnapshot()
    snap.env_vars = {}
    snap.pip_packages = []
    snap.python_version = ""
    snap.node_version = "18.0.0"
    result = filter_snapshot(snap)
    assert result.snapshot.node_version == "18.0.0"


def test_filter_by_value_predicate():
    snap = EnvSnapshot()
    snap.env_vars = {"A": "keep", "B": "drop", "C": "keep"}
    snap.pip_packages = []
    snap.python_version = ""
    result = filter_env_vars(snap, lambda k, v: v == "keep")
    assert set(result.snapshot.env_vars.keys()) == {"A", "C"}


def test_filter_pkg_by_version_prefix():
    snap = EnvSnapshot()
    snap.env_vars = {}
    snap.pip_packages = [
        {"name": "alpha", "version": "1.0.0"},
        {"name": "beta", "version": "2.0.0"},
        {"name": "gamma", "version": "1.5.0"},
    ]
    snap.python_version = ""
    result = filter_pip_packages(snap, lambda p: p["version"].startswith("1"))
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "alpha" in names
    assert "gamma" in names
    assert "beta" not in names
