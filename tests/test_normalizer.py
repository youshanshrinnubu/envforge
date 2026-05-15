"""Tests for envforge.normalizer."""

from __future__ import annotations

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.normalizer import (
    NormalizeResult,
    normalize_env_var_keys,
    normalize_package_names,
    normalize_snapshot,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"path": "/usr/bin", "Home": "/root", "ALREADY": "yes"},
        pip_packages=[
            {"name": "Requests", "version": "2.28.0"},
            {"name": "my_package", "version": "1.0.0"},
            {"name": "flask", "version": "2.0.0"},
        ],
        python_version="3.11.0",
        node_version=None,
    )


def test_normalize_env_var_keys_uppercases(sample_snapshot):
    result = normalize_env_var_keys(sample_snapshot)
    assert "PATH" in result.snapshot.env_vars
    assert "HOME" in result.snapshot.env_vars
    assert "ALREADY" in result.snapshot.env_vars


def test_normalize_env_var_keys_records_changes(sample_snapshot):
    result = normalize_env_var_keys(sample_snapshot)
    assert any("path" in c for c in result.changes)
    assert any("Home" in c for c in result.changes)


def test_normalize_env_var_keys_no_change_for_already_upper(sample_snapshot):
    result = normalize_env_var_keys(sample_snapshot)
    assert not any("ALREADY" in c for c in result.changes)


def test_normalize_env_var_keys_preserves_values(sample_snapshot):
    result = normalize_env_var_keys(sample_snapshot)
    assert result.snapshot.env_vars["PATH"] == "/usr/bin"


def test_normalize_env_var_keys_does_not_mutate_original(sample_snapshot):
    normalize_env_var_keys(sample_snapshot)
    assert "path" in sample_snapshot.env_vars


def test_normalize_package_names_lowercases(sample_snapshot):
    result = normalize_package_names(sample_snapshot)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "requests" in names


def test_normalize_package_names_replaces_underscores(sample_snapshot):
    result = normalize_package_names(sample_snapshot)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "my-package" in names
    assert "my_package" not in names


def test_normalize_package_names_records_changes(sample_snapshot):
    result = normalize_package_names(sample_snapshot)
    assert any("Requests" in c for c in result.changes)
    assert any("my_package" in c for c in result.changes)


def test_normalize_package_names_preserves_versions(sample_snapshot):
    result = normalize_package_names(sample_snapshot)
    by_name = {p["name"]: p for p in result.snapshot.pip_packages}
    assert by_name["requests"]["version"] == "2.28.0"


def test_normalize_snapshot_applies_all_passes(sample_snapshot):
    result = normalize_snapshot(sample_snapshot)
    assert "PATH" in result.snapshot.env_vars
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "requests" in names
    assert "my-package" in names


def test_normalize_snapshot_bool_true_when_changes(sample_snapshot):
    result = normalize_snapshot(sample_snapshot)
    assert bool(result) is True


def test_normalize_snapshot_bool_false_when_clean():
    clean = EnvSnapshot(
        env_vars={"PATH": "/usr/bin"},
        pip_packages=[{"name": "flask", "version": "2.0.0"}],
        python_version="3.11.0",
    )
    result = normalize_snapshot(clean)
    assert bool(result) is False
    assert result.changes == []


def test_normalize_result_counts(sample_snapshot):
    result = normalize_snapshot(sample_snapshot)
    assert result.original_count > 0
    assert result.normalized_count > 0
