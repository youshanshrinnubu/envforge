"""Tests for envforge.filterer."""
from __future__ import annotations

import pytest

from envforge.filterer import (
    FilterResult,
    filter_env_vars,
    filter_pip_packages,
    filter_snapshot,
)
from envforge.snapshot import EnvSnapshot


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    snap = EnvSnapshot()
    snap.env_vars = {
        "HOME": "/home/user",
        "AWS_ACCESS_KEY_ID": "AKIA123",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "PATH": "/usr/bin",
    }
    snap.pip_packages = [
        {"name": "requests", "version": "2.31.0"},
        {"name": "boto3", "version": "1.34.0"},
        {"name": "flask", "version": "3.0.0"},
    ]
    snap.python_version = "3.11.4"
    return snap


def test_filter_result_bool_true_when_filtered(sample_snapshot):
    result = filter_env_vars(sample_snapshot, lambda k, v: k.startswith("AWS"))
    assert bool(result) is True


def test_filter_result_bool_false_when_nothing_removed(sample_snapshot):
    result = filter_env_vars(sample_snapshot, lambda k, v: True)
    assert bool(result) is False


def test_filter_env_vars_keeps_matching(sample_snapshot):
    result = filter_env_vars(sample_snapshot, lambda k, v: k.startswith("AWS"))
    assert set(result.snapshot.env_vars.keys()) == {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}


def test_filter_env_vars_removes_non_matching(sample_snapshot):
    result = filter_env_vars(sample_snapshot, lambda k, v: k == "HOME")
    assert "AWS_ACCESS_KEY_ID" not in result.snapshot.env_vars
    assert "HOME" in result.snapshot.env_vars


def test_filter_env_vars_counts_correct(sample_snapshot):
    result = filter_env_vars(sample_snapshot, lambda k, v: k.startswith("AWS"))
    assert result.original_env_count == 4
    assert result.filtered_env_count == 2


def test_filter_pip_packages_keeps_matching(sample_snapshot):
    result = filter_pip_packages(sample_snapshot, lambda p: p["name"] != "boto3")
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "boto3" not in names
    assert "requests" in names


def test_filter_pip_packages_counts_correct(sample_snapshot):
    result = filter_pip_packages(sample_snapshot, lambda p: p["name"] == "flask")
    assert result.original_pkg_count == 3
    assert result.filtered_pkg_count == 1


def test_filter_snapshot_applies_both(sample_snapshot):
    result = filter_snapshot(
        sample_snapshot,
        env_predicate=lambda k, v: not k.startswith("AWS"),
        pkg_predicate=lambda p: p["name"] == "requests",
    )
    assert "AWS_ACCESS_KEY_ID" not in result.snapshot.env_vars
    assert len(result.snapshot.pip_packages) == 1
    assert result.snapshot.pip_packages[0]["name"] == "requests"


def test_filter_snapshot_applied_filters_recorded(sample_snapshot):
    result = filter_snapshot(
        sample_snapshot,
        env_predicate=lambda k, v: True,
        pkg_predicate=lambda p: True,
    )
    assert "env_vars" in result.applied_filters
    assert "pip_packages" in result.applied_filters


def test_filter_snapshot_no_predicates_is_noop(sample_snapshot):
    result = filter_snapshot(sample_snapshot)
    assert result.original_env_count == result.filtered_env_count
    assert result.original_pkg_count == result.filtered_pkg_count
    assert result.applied_filters == []


def test_filter_does_not_mutate_original(sample_snapshot):
    original_env = dict(sample_snapshot.env_vars)
    filter_env_vars(sample_snapshot, lambda k, v: False)
    assert sample_snapshot.env_vars == original_env
