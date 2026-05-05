"""Tests for snapshot capture and serialization."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from envforge.snapshot import (
    EnvSnapshot,
    capture_env_vars,
    take_snapshot,
)
from envforge.serializer import (
    save_snapshot,
    load_snapshot,
    snapshot_to_dict,
    snapshot_from_dict,
    SNAPSHOT_VERSION,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        shell="/bin/bash",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        installed_packages=["requests==2.31.0", "pytest==8.0.0"],
        python_version="Python 3.12.0",
        node_version="v20.0.0",
        working_directory="/home/user/project",
    )


def test_capture_env_vars_excludes_keys():
    with patch.dict("os.environ", {"MY_VAR": "hello", "PS1": "$ "}):
        result = capture_env_vars()
        assert "MY_VAR" in result
        assert "PS1" not in result


def test_capture_env_vars_custom_exclude():
    with patch.dict("os.environ", {"SECRET": "abc", "PATH": "/usr/bin"}):
        result = capture_env_vars(exclude_keys=["SECRET"])
        assert "SECRET" not in result
        assert "PATH" in result


def test_snapshot_to_dict_contains_version(sample_snapshot):
    d = snapshot_to_dict(sample_snapshot)
    assert d["version"] == SNAPSHOT_VERSION
    assert d["shell"] == "/bin/bash"
    assert d["python_version"] == "Python 3.12.0"


def test_snapshot_roundtrip(sample_snapshot):
    d = snapshot_to_dict(sample_snapshot)
    restored = snapshot_from_dict(d)
    assert restored.shell == sample_snapshot.shell
    assert restored.env_vars == sample_snapshot.env_vars
    assert restored.installed_packages == sample_snapshot.installed_packages
    assert restored.python_version == sample_snapshot.python_version


def test_snapshot_from_dict_invalid_version():
    with pytest.raises(ValueError, match="Unsupported snapshot version"):
        snapshot_from_dict({"version": "0.1", "shell": "/bin/sh"})


def test_save_and_load_snapshot(tmp_path, sample_snapshot):
    out_file = tmp_path / "env.json"
    save_snapshot(sample_snapshot, out_file)
    assert out_file.exists()
    loaded = load_snapshot(out_file)
    assert loaded.shell == sample_snapshot.shell
    assert loaded.node_version == sample_snapshot.node_version
    assert loaded.installed_packages == sample_snapshot.installed_packages


def test_load_snapshot_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "nonexistent.json")


def test_take_snapshot_returns_env_snapshot():
    snapshot = take_snapshot()
    assert isinstance(snapshot, EnvSnapshot)
    assert isinstance(snapshot.env_vars, dict)
    assert isinstance(snapshot.installed_packages, list)
    assert snapshot.shell != ""
