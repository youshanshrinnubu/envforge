"""Tests for envforge.pinner module."""

import pytest
from envforge.snapshot import EnvSnapshot
from envforge.pinner import (
    pin_packages,
    unpin_packages,
    pin_env_vars,
    list_pinned,
    PINNED_MARKER,
)


@pytest.fixture
def sample_snapshot():
    snap = EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/root", "DEBUG": "1"},
        python_version="3.11.2",
        node_version="18.0.0",
        pip_packages={"requests": "2.28.0", "flask": "2.3.1", "numpy": "1.24.0"},
    )
    snap.pinned_env_vars = []
    return snap


def test_pin_packages_marks_version(sample_snapshot):
    result = pin_packages(sample_snapshot, ["requests"])
    assert "requests" in result.pinned_packages
    assert sample_snapshot.pip_packages["requests"] == f"{PINNED_MARKER}2.28.0"


def test_pin_packages_multiple(sample_snapshot):
    result = pin_packages(sample_snapshot, ["requests", "flask"])
    assert len(result.pinned_packages) == 2
    assert sample_snapshot.pip_packages["flask"].startswith(PINNED_MARKER)


def test_pin_packages_skips_missing(sample_snapshot):
    result = pin_packages(sample_snapshot, ["nonexistent"])
    assert "nonexistent" in result.skipped
    assert result.pinned_packages == []


def test_pin_packages_idempotent(sample_snapshot):
    pin_packages(sample_snapshot, ["requests"])
    pin_packages(sample_snapshot, ["requests"])
    val = sample_snapshot.pip_packages["requests"]
    assert val.count(PINNED_MARKER) == 1


def test_unpin_packages_removes_marker(sample_snapshot):
    pin_packages(sample_snapshot, ["numpy"])
    result = unpin_packages(sample_snapshot, ["numpy"])
    assert "numpy" in result.pinned_packages
    assert sample_snapshot.pip_packages["numpy"] == "1.24.0"


def test_unpin_packages_skips_missing(sample_snapshot):
    result = unpin_packages(sample_snapshot, ["ghost"])
    assert "ghost" in result.skipped


def test_unpin_already_unpinned_is_safe(sample_snapshot):
    result = unpin_packages(sample_snapshot, ["flask"])
    assert "flask" in result.pinned_packages
    assert sample_snapshot.pip_packages["flask"] == "2.3.1"


def test_pin_env_vars_adds_to_list(sample_snapshot):
    result = pin_env_vars(sample_snapshot, ["PATH", "HOME"])
    assert "PATH" in result.pinned_env_vars
    assert "HOME" in result.pinned_env_vars
    assert set(sample_snapshot.pinned_env_vars) >= {"PATH", "HOME"}


def test_pin_env_vars_skips_absent(sample_snapshot):
    result = pin_env_vars(sample_snapshot, ["MISSING_VAR"])
    assert "MISSING_VAR" in result.skipped


def test_list_pinned_returns_correct_structure(sample_snapshot):
    pin_packages(sample_snapshot, ["requests"])
    pin_env_vars(sample_snapshot, ["DEBUG"])
    summary = list_pinned(sample_snapshot)
    assert "packages" in summary
    assert "env_vars" in summary
    assert summary["packages"]["requests"] == "2.28.0"
    assert "DEBUG" in summary["env_vars"]


def test_list_pinned_empty(sample_snapshot):
    summary = list_pinned(sample_snapshot)
    assert summary["packages"] == {}
    assert summary["env_vars"] == []
