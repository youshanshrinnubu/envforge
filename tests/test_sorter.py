"""Tests for envforge.sorter."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.sorter import (
    SortResult,
    sort_env_vars,
    sort_pip_packages,
    sort_snapshot,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"ZEBRA": "1", "APPLE": "2", "MANGO": "3"},
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages=[
            {"name": "requests", "version": "2.28.0"},
            {"name": "boto3", "version": "1.26.0"},
            {"name": "flask", "version": "2.3.0"},
        ],
        label="test",
    )


def test_sort_result_bool_true_when_fields_sorted(sample_snapshot):
    result = sort_env_vars(sample_snapshot)
    assert bool(result) is True


def test_sort_result_bool_false_on_empty_snapshot():
    empty = EnvSnapshot(env_vars={}, python_version=None, node_version=None, pip_packages=[])
    result = sort_env_vars(empty)
    assert bool(result) is False


def test_sort_env_vars_ascending(sample_snapshot):
    result = sort_env_vars(sample_snapshot, order="asc")
    keys = list(result.snapshot.env_vars.keys())
    assert keys == sorted(keys)


def test_sort_env_vars_descending(sample_snapshot):
    result = sort_env_vars(sample_snapshot, order="desc")
    keys = list(result.snapshot.env_vars.keys())
    assert keys == sorted(keys, reverse=True)


def test_sort_env_vars_does_not_mutate_original(sample_snapshot):
    original_keys = list(sample_snapshot.env_vars.keys())
    sort_env_vars(sample_snapshot, order="asc")
    assert list(sample_snapshot.env_vars.keys()) == original_keys


def test_sort_pip_packages_ascending_by_name(sample_snapshot):
    result = sort_pip_packages(sample_snapshot, order="asc", key="name")
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert names == sorted(names)


def test_sort_pip_packages_descending_by_name(sample_snapshot):
    result = sort_pip_packages(sample_snapshot, order="desc", key="name")
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert names == sorted(names, reverse=True)


def test_sort_pip_packages_does_not_mutate_original(sample_snapshot):
    original = [p["name"] for p in sample_snapshot.pip_packages]
    sort_pip_packages(sample_snapshot, order="asc")
    assert [p["name"] for p in sample_snapshot.pip_packages] == original


def test_sort_pip_packages_fields_sorted_recorded(sample_snapshot):
    result = sort_pip_packages(sample_snapshot)
    assert "pip_packages" in result.fields_sorted


def test_sort_snapshot_sorts_both_fields(sample_snapshot):
    result = sort_snapshot(sample_snapshot, order="asc")
    assert "env_vars" in result.fields_sorted
    assert "pip_packages" in result.fields_sorted


def test_sort_snapshot_order_recorded(sample_snapshot):
    result = sort_snapshot(sample_snapshot, order="desc")
    assert result.order == "desc"


def test_sort_snapshot_selective_fields(sample_snapshot):
    result = sort_snapshot(sample_snapshot, fields=["env_vars"])
    assert "env_vars" in result.fields_sorted
    assert "pip_packages" not in result.fields_sorted


def test_sort_snapshot_preserves_versions(sample_snapshot):
    result = sort_snapshot(sample_snapshot)
    assert result.snapshot.python_version == sample_snapshot.python_version
    assert result.snapshot.node_version == sample_snapshot.node_version
    assert result.snapshot.label == sample_snapshot.label
