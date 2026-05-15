"""Tests for envforge.deduplicator."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.deduplicator import (
    DeduplicateResult,
    deduplicate_pip_packages,
    deduplicate_env_vars,
    deduplicate_snapshot,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/root", "path": "/duplicate"},
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages=[
            {"name": "requests", "version": "2.28.0"},
            {"name": "flask", "version": "2.3.0"},
            {"name": "Requests", "version": "2.31.0"},
        ],
        label="test",
    )


def test_deduplicate_result_bool_true_when_removed(sample_snapshot):
    result = deduplicate_pip_packages(sample_snapshot)
    assert bool(result) is True


def test_deduplicate_result_bool_false_when_nothing_removed():
    snap = EnvSnapshot(
        env_vars={"HOME": "/root"},
        python_version="3.11.0",
        pip_packages=[{"name": "flask", "version": "2.3.0"}],
    )
    result = deduplicate_pip_packages(snap)
    assert bool(result) is False


def test_deduplicate_pip_packages_removes_earlier_duplicate(sample_snapshot):
    result = deduplicate_pip_packages(sample_snapshot)
    names = [p["name"].lower() for p in result.snapshot.pip_packages]
    assert names.count("requests") == 1


def test_deduplicate_pip_packages_keeps_last_occurrence(sample_snapshot):
    result = deduplicate_pip_packages(sample_snapshot)
    kept = next(p for p in result.snapshot.pip_packages if p["name"].lower() == "requests")
    assert kept["version"] == "2.31.0"


def test_deduplicate_pip_packages_records_removed(sample_snapshot):
    result = deduplicate_pip_packages(sample_snapshot)
    assert "requests" in result.removed_packages


def test_deduplicate_pip_packages_preserves_unique(sample_snapshot):
    result = deduplicate_pip_packages(sample_snapshot)
    names = [p["name"].lower() for p in result.snapshot.pip_packages]
    assert "flask" in names


def test_deduplicate_env_vars_removes_case_duplicate(sample_snapshot):
    result = deduplicate_env_vars(sample_snapshot)
    keys_lower = [k.lower() for k in result.snapshot.env_vars]
    assert keys_lower.count("path") == 1


def test_deduplicate_env_vars_records_removed_key(sample_snapshot):
    result = deduplicate_env_vars(sample_snapshot)
    assert "path" in result.removed_env_keys


def test_deduplicate_env_vars_keeps_first_occurrence(sample_snapshot):
    result = deduplicate_env_vars(sample_snapshot)
    assert result.snapshot.env_vars.get("PATH") == "/usr/bin"


def test_deduplicate_snapshot_combines_both(sample_snapshot):
    result = deduplicate_snapshot(sample_snapshot)
    assert "requests" in result.removed_packages
    assert "path" in result.removed_env_keys


def test_deduplicate_snapshot_does_not_mutate_original(sample_snapshot):
    original_pkg_count = len(sample_snapshot.pip_packages)
    deduplicate_snapshot(sample_snapshot)
    assert len(sample_snapshot.pip_packages) == original_pkg_count


def test_deduplicate_empty_snapshot():
    snap = EnvSnapshot(env_vars={}, python_version=None, pip_packages=[])
    result = deduplicate_snapshot(snap)
    assert not result.removed_packages
    assert not result.removed_env_keys
    assert bool(result) is False
