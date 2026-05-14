"""Tests for envforge.migrator."""

from __future__ import annotations

import pytest

from envforge.migrator import (
    CURRENT_SCHEMA_VERSION,
    MigrationResult,
    detect_version,
    migrate_dict,
    migrate_snapshot,
)
from envforge.snapshot import EnvSnapshot


@pytest.fixture()
def v0_data():
    return {
        "schema_version": 0,
        "label": "old-snap",
        "env_vars": {"HOME": "/home/user"},
        "pip_packages": ["requests==2.28.0", "flask==2.2.0"],
        "python_version": "3.10.0",
        "node_version": None,
        "shell": "bash",
    }


@pytest.fixture()
def v1_data():
    return {
        "schema_version": 1,
        "label": "mid-snap",
        "env_vars": {"HOME": "/home/user"},
        "pip_packages": [{"name": "requests", "version": "2.28.0"}],
        "python_version": "3.10.0",
        "node": "18.0.0",
        "shell": "bash",
    }


def test_detect_version_explicit(v0_data):
    assert detect_version(v0_data) == 0


def test_detect_version_defaults_to_zero():
    assert detect_version({}) == 0


def test_detect_version_v1(v1_data):
    assert detect_version(v1_data) == 1


def test_migrate_dict_v0_normalises_packages(v0_data):
    result = migrate_dict(v0_data, target_version=1)
    pkgs = result.snapshot.pip_packages
    assert all(isinstance(p, dict) for p in pkgs)
    assert pkgs[0]["name"] == "requests"
    assert pkgs[0]["version"] == "2.28.0"


def test_migrate_dict_v1_renames_node_key(v1_data):
    result = migrate_dict(v1_data, target_version=2)
    assert result.snapshot.node_version == "18.0.0"


def test_migrate_dict_full_pipeline(v0_data):
    result = migrate_dict(v0_data, target_version=CURRENT_SCHEMA_VERSION)
    assert len(result.steps_applied) == CURRENT_SCHEMA_VERSION
    assert result.original_version == 0
    assert result.target_version == CURRENT_SCHEMA_VERSION


def test_migration_result_bool_true_when_migrated(v0_data):
    result = migrate_dict(v0_data)
    assert bool(result) is True


def test_migration_result_bool_false_when_already_current():
    from envforge.serializer import snapshot_to_dict

    snap = EnvSnapshot(
        label="current",
        env_vars={},
        pip_packages=[],
        python_version="3.11.0",
        node_version=None,
        shell="zsh",
    )
    data = snapshot_to_dict(snap)
    data["schema_version"] = CURRENT_SCHEMA_VERSION
    result = migrate_dict(data, target_version=CURRENT_SCHEMA_VERSION)
    assert bool(result) is False


def test_migrate_snapshot_convenience():
    snap = EnvSnapshot(
        label="old",
        env_vars={"X": "1"},
        pip_packages=[{"name": "numpy", "version": "1.24.0"}],
        python_version="3.9.0",
        node_version=None,
        shell="sh",
    )
    result = migrate_snapshot(snap, source_version=1)
    assert isinstance(result, MigrationResult)
    assert result.original_version == 1


def test_migrate_dict_no_migration_needed_returns_snapshot(v1_data):
    # Migrate only one step
    result = migrate_dict(v1_data, target_version=2)
    assert isinstance(result.snapshot, EnvSnapshot)
    assert "v1->v2" in result.steps_applied[0]


def test_migrate_dict_unknown_version_adds_warning():
    data = {"schema_version": 99, "label": "x", "env_vars": {},
            "pip_packages": [], "python_version": None,
            "node_version": None, "shell": None}
    result = migrate_dict(data, target_version=100)
    assert result.warnings
