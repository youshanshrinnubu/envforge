"""Tests for envforge.history module."""

import json
import pytest
from pathlib import Path

from envforge.snapshot import EnvSnapshot
from envforge.history import (
    get_history_dir,
    record_snapshot,
    list_history,
    load_history_entry,
    delete_history_entry,
)


@pytest.fixture
def tmp_history_dir(tmp_path):
    return tmp_path / "history"


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        python_version="3.11.4",
        node_version="18.0.0",
        pip_packages={"requests": "2.31.0", "flask": "3.0.0"},
        shell="bash",
    )


def test_get_history_dir_default():
    hdir = get_history_dir()
    assert str(hdir).endswith(".envforge/history")


def test_get_history_dir_custom(tmp_path):
    hdir = get_history_dir(tmp_path)
    assert hdir == tmp_path


def test_record_snapshot_creates_file(sample_snapshot, tmp_history_dir):
    path = record_snapshot(sample_snapshot, history_dir=tmp_history_dir)
    assert path.exists()
    assert path.suffix == ".json"


def test_record_snapshot_with_label(sample_snapshot, tmp_history_dir):
    path = record_snapshot(sample_snapshot, label="myenv", history_dir=tmp_history_dir)
    assert "myenv" in path.name


def test_record_snapshot_stores_metadata(sample_snapshot, tmp_history_dir):
    path = record_snapshot(sample_snapshot, label="ci", history_dir=tmp_history_dir)
    with open(path) as f:
        data = json.load(f)
    assert "_history" in data
    assert data["_history"]["label"] == "ci"
    assert data["_history"]["timestamp"]


def test_list_history_empty(tmp_history_dir):
    entries = list_history(history_dir=tmp_history_dir)
    assert entries == []


def test_list_history_returns_entries(sample_snapshot, tmp_history_dir):
    record_snapshot(sample_snapshot, label="first", history_dir=tmp_history_dir)
    record_snapshot(sample_snapshot, label="second", history_dir=tmp_history_dir)
    entries = list_history(history_dir=tmp_history_dir)
    assert len(entries) == 2
    assert all("filename" in e for e in entries)
    assert all("timestamp" in e for e in entries)


def test_list_history_sorted_newest_first(sample_snapshot, tmp_history_dir):
    record_snapshot(sample_snapshot, label="alpha", history_dir=tmp_history_dir)
    record_snapshot(sample_snapshot, label="beta", history_dir=tmp_history_dir)
    entries = list_history(history_dir=tmp_history_dir)
    assert entries[0]["filename"] > entries[1]["filename"]


def test_load_history_entry_roundtrip(sample_snapshot, tmp_history_dir):
    path = record_snapshot(sample_snapshot, label="load_test", history_dir=tmp_history_dir)
    loaded = load_history_entry(path.name, history_dir=tmp_history_dir)
    assert loaded.python_version == sample_snapshot.python_version
    assert loaded.pip_packages == sample_snapshot.pip_packages
    assert loaded.env_vars == sample_snapshot.env_vars


def test_load_history_entry_not_found(tmp_history_dir):
    with pytest.raises(FileNotFoundError):
        load_history_entry("nonexistent.json", history_dir=tmp_history_dir)


def test_delete_history_entry(sample_snapshot, tmp_history_dir):
    path = record_snapshot(sample_snapshot, history_dir=tmp_history_dir)
    delete_history_entry(path.name, history_dir=tmp_history_dir)
    assert not path.exists()


def test_delete_history_entry_not_found(tmp_history_dir):
    with pytest.raises(FileNotFoundError):
        delete_history_entry("ghost.json", history_dir=tmp_history_dir)
