"""Tests for envforge.trimmer."""
from __future__ import annotations

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.trimmer import (
    TrimResult,
    trim_empty_env_vars,
    trim_packages_without_version,
    trim_snapshot,
)


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={
            "HOME": "/home/user",
            "EMPTY_VAR": "",
            "SPACES_VAR": "   ",
            "PATH": "/usr/bin",
        },
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages=[
            {"name": "requests", "version": "2.28.0"},
            {"name": "unpinned", "version": ""},
            {"name": "also-unpinned", "version": None},
            {"name": "flask", "version": "2.3.0"},
        ],
        label="test",
    )


@pytest.fixture()
def empty_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={},
        python_version=None,
        node_version=None,
        pip_packages=[],
        label=None,
    )


# --- TrimResult bool ---

def test_trim_result_bool_true_when_removed():
    snap = EnvSnapshot(env_vars={}, pip_packages=[])
    r = TrimResult(snapshot=snap, removed_env_vars=["X"])
    assert bool(r) is True


def test_trim_result_bool_false_when_nothing_removed():
    snap = EnvSnapshot(env_vars={}, pip_packages=[])
    r = TrimResult(snapshot=snap)
    assert bool(r) is False


# --- trim_empty_env_vars ---

def test_trim_empty_env_vars_removes_empty_string(sample_snapshot):
    result = trim_empty_env_vars(sample_snapshot)
    assert "EMPTY_VAR" not in result.snapshot.env_vars


def test_trim_empty_env_vars_removes_whitespace_only(sample_snapshot):
    result = trim_empty_env_vars(sample_snapshot)
    assert "SPACES_VAR" not in result.snapshot.env_vars


def test_trim_empty_env_vars_preserves_non_empty(sample_snapshot):
    result = trim_empty_env_vars(sample_snapshot)
    assert result.snapshot.env_vars["HOME"] == "/home/user"
    assert result.snapshot.env_vars["PATH"] == "/usr/bin"


def test_trim_empty_env_vars_records_removed_keys(sample_snapshot):
    result = trim_empty_env_vars(sample_snapshot)
    assert "EMPTY_VAR" in result.removed_env_vars
    assert "SPACES_VAR" in result.removed_env_vars


def test_trim_empty_env_vars_no_change_on_empty_snapshot(empty_snapshot):
    result = trim_empty_env_vars(empty_snapshot)
    assert bool(result) is False
    assert result.removed_env_vars == []


# --- trim_packages_without_version ---

def test_trim_packages_without_version_removes_empty_version(sample_snapshot):
    result = trim_packages_without_version(sample_snapshot)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "unpinned" not in names
    assert "also-unpinned" not in names


def test_trim_packages_without_version_keeps_pinned(sample_snapshot):
    result = trim_packages_without_version(sample_snapshot)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "requests" in names
    assert "flask" in names


def test_trim_packages_without_version_records_removed(sample_snapshot):
    result = trim_packages_without_version(sample_snapshot)
    assert "unpinned" in result.removed_packages
    assert "also-unpinned" in result.removed_packages


# --- trim_snapshot (combined) ---

def test_trim_snapshot_combines_both_passes(sample_snapshot):
    result = trim_snapshot(sample_snapshot)
    assert "EMPTY_VAR" not in result.snapshot.env_vars
    assert "SPACES_VAR" not in result.snapshot.env_vars
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "unpinned" not in names


def test_trim_snapshot_messages_include_all(sample_snapshot):
    result = trim_snapshot(sample_snapshot)
    combined = " ".join(result.messages)
    assert "EMPTY_VAR" in combined
    assert "unpinned" in combined


def test_trim_snapshot_does_not_mutate_original(sample_snapshot):
    _ = trim_snapshot(sample_snapshot)
    assert "EMPTY_VAR" in sample_snapshot.env_vars
